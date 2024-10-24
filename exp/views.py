from django import forms
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
import pandas as pd
import sqlite3
import os
import re

from transformers import AutoTokenizer, AutoModelForCausalLM

from project.serializers import QuerySerializer

# Global variable to store CSV data as a DataFrame
csv_data = {}
# Assume global variables for storing the uploaded table name and CSV data
global uploaded_table_name, csv_dat
uploaded_table_name = None
csv_dat = None
# Form for uploading CSV
class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label='Select a CSV file', required=True)

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.endswith('.csv'):
            raise forms.ValidationError('Invalid file type. Please upload a CSV file.')
        return csv_file


# View for uploading CSVclass UploadCSVView(APIView):
class UploadCSVView(APIView):
    def post(self, request):
        global uploaded_table_name, csv_dat  # Access the global variable to store CSV data
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            try:
                # Parse the CSV file into a Pandas DataFrame
                df = pd.read_csv(csv_file)

                # Store the DataFrame directly in the global variable
                csv_dat = df

                # Connect to (or create) an SQLite database
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()

                # Mapping pandas data types to SQLite types
                def map_dtype(dtype):
                    if dtype == 'string':
                        return 'TEXT'
                    elif dtype == 'integer':
                        return 'INTEGER'
                    elif dtype == 'floating':
                        return 'REAL'
                    elif dtype == 'boolean':
                        return 'BOOLEAN'
                    elif dtype == 'datetime64[ns]':
                        return 'DATETIME'
                    elif dtype == 'datetime64[ns, UTC]':
                        return 'DATETIME'
                    elif dtype == 'timedelta64[ns]':
                        return 'TEXT'  # SQLite doesn't have a native timedelta type, so we store it as TEXT
                    elif dtype == 'category':
                        return 'TEXT'  # Categories are stored as TEXT
                    elif dtype == 'date':
                        return 'DATE'
                    else:
                        return 'TEXT'  # Default to TEXT if unknown type

                # Generate the table name from the CSV file name (without extension)
                uploaded_table_name = os.path.splitext(csv_file.name)[0]  # Set the table name here

                # Generate a CREATE TABLE statement based on the DataFrame's columns and types
                columns = ', '.join([f'{col} {map_dtype(pd.api.types.infer_dtype(df[col], skipna=True))}' for col in df.columns])

                # Create the table schema in SQLite
                create_table_query = f"CREATE TABLE IF NOT EXISTS {uploaded_table_name} ({columns});"
                cursor.execute(create_table_query)

                # Insert data from the DataFrame into the SQLite table
                df.to_sql(uploaded_table_name, conn, if_exists='replace', index=False)

                # Commit changes and close the connection
                conn.commit()
                conn.close()

                # Return column names and the dynamic table name as part of the response
                column_names = df.columns.tolist()
                return Response({'message': 'CSV file uploaded and table created successfully', 'columns': column_names, 'table_name': uploaded_table_name}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({'error': f"Error processing the CSV file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid form submission'}, status=status.HTTP_400_BAD_REQUEST)

class GenerateSQlQuery(APIView):
    def post(self, request):
        serializer = QuerySerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data['text']
            try:
                if uploaded_table_name is None or csv_dat is None:
                    return Response({'error': 'No table has been uploaded yet.'},
                                    status=status.HTTP_400_BAD_REQUEST)

                # Generate the SQL query
                generated_sql = self.generate_sql_query_for_table(prompt)

                if not generated_sql:
                    return Response({'error': 'Generated SQL query is empty.'},
                                    status=status.HTTP_400_BAD_REQUEST)

                # Execute the generated SQL query and get results
                result = self.execute_sql_query(generated_sql)

                return Response({'sql_query': generated_sql, 'results': result}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def generate_sql_query_for_table(self, prompt):
        global uploaded_table_name, csv_dat  # Access the uploaded table name and CSV data
        if uploaded_table_name is None or csv_dat is None:
            raise Exception("No table or data has been uploaded.")

        table_name = uploaded_table_name  # Get the table name from the global variable
        columns = csv_dat.columns.tolist()  # Dynamically fetch the column names from the uploaded CSV

        # Using the table name and dynamic columns in the prompt for SQL generation
        tokenizer = AutoTokenizer.from_pretrained("NumbersStation/nsql-350M")
        model = AutoModelForCausalLM.from_pretrained("NumbersStation/nsql-350M")

        # Dynamically constructing the table structure for SQL generation
        column_structure = ', '.join([f'{col}' for col in columns])
        text = f"""
        -- Using valid SQLite, answer the following question based on the below table structure:

        -- Table name: {table_name}
        -- Columns: {column_structure}

        -- {prompt}

        SELECT"""

        input_ids = tokenizer(text, return_tensors="pt").input_ids
        generated_ids = model.generate(input_ids, max_length=500)
        generated_sql = tokenizer.decode(generated_ids[0], skip_special_tokens=True).strip()

        # Ensure the SQL query is valid and clean
        generated_sql = self.sanitize_query(generated_sql)

        # Log the generated SQL query for debugging
        print(f"Generated SQL Query: {generated_sql}")

        return generated_sql

    def sanitize_query(self, query):
        # Strip unnecessary white spaces and comments
        query = query.strip()
        query = '\n'.join([line for line in query.split('\n') if not line.strip().startswith('--')])
        # Ensure only a single SQL statement
        statements = query.split(';')
        if len(statements) > 1:
            # Log warning if multiple statements are detected
            print("Warning: Multiple SQL statements detected. Only the first statement will be executed.")
        return statements[0].strip()  # Return the first statement only

    def execute_sql_query(self, sql_query):
        try:
            # Assuming SQLite connection here
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            # Execute the SQL query
            cursor.execute(sql_query)
            rows = cursor.fetchall()

            if not rows:
                return {"message": "No results found"}

            # Optionally, get column names
            column_names = [desc[0] for desc in cursor.description]

            # Format the result in a list of dictionaries
            result = [dict(zip(column_names, row)) for row in rows]

            conn.close()
            return result
        except Exception as e:
            # Handle SQL errors or other exceptions
            raise Exception(f"SQL execution error: {str(e)}")


# multiple

uploaded_table_info = []
# Global variable to store table information


class MultipleCSVUploadView(APIView):
    def post(self, request):
        global uploaded_table_info  # Use global variable

        csv_files = request.FILES.getlist('csv_files')
        success_files = []
        failed_files = []

        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                table_name = re.sub(r'\W|^(?=\d)', '_', os.path.splitext(csv_file.name)[0])

                with sqlite3.connect('database.db') as conn:
                    df.to_sql(table_name, conn, if_exists='replace', index=False)

                uploaded_table_info.append({'table_name': table_name, 'columns': df.columns.tolist()})
                success_files.append({'table_name': table_name, 'columns': df.columns.tolist()})

            except Exception as e:
                failed_files.append({'file_name': csv_file.name, 'error': str(e)})

        return Response({
            'message': 'Files processed.',
            'successful_files': success_files,
            'failed_files': failed_files
        }, status=status.HTTP_200_OK)

