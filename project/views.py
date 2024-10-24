import csv
from datetime import datetime
from io import TextIOWrapper
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Purchase, Customer, Sales
from .serializers import PurchaseSerializer, QuerySerializer, CustomerSerializer, SalesSerializer
from transformers import AutoTokenizer, AutoModelForCausalLM
from django.db import connection
import re



# products
# for uploading product purchase csv file
class UploadCSV(APIView):
    def post(self, request):
        csv_file = request.FILES.get('csv_file')

        if not csv_file or not csv_file.name.endswith('.csv'):
            return Response({"error": "Please upload a valid CSV file."}, status=status.HTTP_400_BAD_REQUEST)

        # Read the CSV file
        file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
        csv_reader = csv.reader(file_data)

        # Skip the header
        next(csv_reader)

        # Date formats to try
        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y']

        # Loop through the rows and save them in the database
        for row in csv_reader:
            item_id, purchase_date_str, name, quantity, price = row
            purchase_date = None

            # Try different date formats
            for date_format in date_formats:
                try:
                    purchase_date = datetime.strptime(purchase_date_str, date_format).date()
                    break
                except ValueError:
                    continue

            if not purchase_date:
                return Response({"error": f"Date format error in row: {row}"}, status=status.HTTP_400_BAD_REQUEST)

            data = {
                'item_id': item_id,
                'purchase_date': purchase_date,
                'name': name,
                'quantity': quantity,
                'price': price
            }
            serializer = PurchaseSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Data successfully uploaded!"}, status=status.HTTP_201_CREATED)



# customer

class Upload_Customer_CSV(APIView):
    def post(self, request):
        csv_file = request.FILES.get('csv_file')

        if not csv_file or not csv_file.name.endswith('.csv'):
            return Response({"error": "Please upload a valid CSV file."}, status=status.HTTP_400_BAD_REQUEST)

        # Read the CSV file
        file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
        csv_reader = csv.reader(file_data)

        # Skip the header
        next(csv_reader)

        # Loop through the rows and save them in the database
        for row in csv_reader:
            # Ensure you are unpacking 3 values only
            if len(row) != 3:
                return Response(
                    {"error": "CSV file must contain exactly 3 columns: customer_name, email, phone_number"},
                    status=status.HTTP_400_BAD_REQUEST)

            # Unpack the values for the 3 columns in your CSV
            customer_name, email, phone_number = row

            # Create a dictionary for the serializer without customer_id
            data = {
                'customer_name': customer_name,
                'email': email,
                'phone_number': phone_number
            }

            # Serialize and validate data
            serializer = CustomerSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Customers data successfully uploaded!"}, status=status.HTTP_201_CREATED)





# Sales
class Upload_Sales_CSV(APIView):
    def post(self, request):
        csv_file = request.FILES.get('csv_file')

        if not csv_file or not csv_file.name.endswith('.csv'):
            return Response({"error": "Please upload a valid CSV file."}, status=status.HTTP_400_BAD_REQUEST)

        # Read the CSV file
        file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
        csv_reader = csv.reader(file_data)

        # Skip the header
        next(csv_reader)

        # Date formats to try
        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y']

        # Loop through the rows and save them in the database
        for row in csv_reader:
            # Ensure you are unpacking 5 values (without sales_id)
            if len(row) != 5:
                return Response({
                    "error": "CSV file must contain exactly 5 columns: customer_id, item_id, quantity, total_price, sales_date"},
                    status=status.HTTP_400_BAD_REQUEST)

            # Unpack the values from the CSV
            customer_id, item_id, quantity, total_price, sales_date_str = row

            # Try to parse the sales_date with multiple formats
            sales_date = None
            for date_format in date_formats:
                try:
                    sales_date = datetime.strptime(sales_date_str, date_format).date()
                    break
                except ValueError:
                    continue

            if sales_date is None:
                return Response(
                    {"error": "Sales date must be in one of the formats: YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY."},
                    status=status.HTTP_400_BAD_REQUEST)

            # Ensure foreign key references are valid
            try:
                customer = Customer.objects.get(customer_id=customer_id)
            except Customer.DoesNotExist:
                return Response({"error": f"Customer with ID {customer_id} does not exist."},
                                status=status.HTTP_400_BAD_REQUEST)

            try:
                item = Purchase.objects.get(item_id=item_id)
            except Purchase.DoesNotExist:
                return Response({"error": f"Purchase item with ID {item_id} does not exist."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Create a dictionary for the serializer
            data = {
                'customer': customer.customer_id,
                'item': item.item_id,
                'quantity': quantity,
                'total_price': total_price,
                'sales_date': sales_date
            }

            path = default_storage.save('uploads/' + csv_file.name, ContentFile(csv_file.read()))

            # Serialize and validate data
            serializer = SalesSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Sales data successfully uploaded!"}, status=status.HTTP_201_CREATED)





# genrating sql queries

# to retrieve sales & customer details together from name, email and phone number
class GenerateSQLQueryView(APIView):
    def post(self, request):
        serializer = QuerySerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data['text']
            try:
                generated_sql = self.generate_sql_query_for_purchase(prompt)
                if not generated_sql:
                    return Response({'error': 'Generated SQL query is empty.'}, status=status.HTTP_400_BAD_REQUEST)

                result = self.execute_sql_query(generated_sql)
                return Response({'sql_query': generated_sql, 'results': result}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def generate_sql_query_for_purchase(self, prompt):
        tokenizer = AutoTokenizer.from_pretrained("NumbersStation/nsql-350M")
        model = AutoModelForCausalLM.from_pretrained("NumbersStation/nsql-350M")

        customer_name = self.extract_field(prompt, "name")
        phone_number = self.extract_field(prompt, "phone number")
        email = self.extract_field(prompt, "email")
        sales_date = self.extract_field(prompt, "sales date")
        total_price = self.extract_field(prompt, "total price")
        item_name = self.extract_field(prompt, "item")

        filters = []
        if customer_name:
            filters.append(f"c.customer_name = '{customer_name}'")
        if phone_number:
            filters.append(f"c.phone_number = '{phone_number}'")
        if email:
            filters.append(f"c.customer_email = '{email}'")
        if sales_date:
            filters.append(f"s.sales_date = '{sales_date}'")
        if total_price:
            filters.append(f"s.total_price = '{total_price}'")
        if item_name:
            filters.append(f"p.name = '{item_name}'")

        where_clause = " AND ".join(filters) if filters else "1=1"

        text = f"""
        -- Using valid SQLite, answer the following question based on the tables structure below:
        -- Table name: project_purchase
        -- Columns: item_id (INTEGER PRIMARY KEY), purchase_date (DATE), name (TEXT), quantity (INTEGER), price (DECIMAL)
        -- Table name: project_customer
        -- Columns: customer_id (INTEGER PRIMARY KEY), customer_name (TEXT), email (TEXT UNIQUE), phone_number (TEXT)
        -- Table name: project_sales
        -- Columns: sales_id (INTEGER PRIMARY KEY), customer_id (INTEGER FOREIGN KEY), item_id (INTEGER FOREIGN KEY), quantity (INTEGER), total_price (DECIMAL), sales_date (DATE)

        SELECT 
            s.sales_id,
            s.quantity,
            s.total_price,
            s.sales_date,
            c.customer_id,
            c.customer_name,
            c.customer_email,
            c.phone_number,
            p.item_id,
            p.name AS item_name,
            p.purchase_date,
            p.price
        FROM 
            project_sales s
        JOIN 
            project_customer c ON s.customer_id = c.customer_id
        JOIN 
            project_purchase p ON s.item_id = p.item_id
        WHERE 
            {where_clause};
        """

        input_ids = tokenizer(text, return_tensors="pt").input_ids
        generated_ids = model.generate(input_ids, max_length=1000)
        generated_sql = tokenizer.decode(generated_ids[0], skip_special_tokens=True).strip()
        generated_sql = self.sanitize_query(generated_sql)

        return generated_sql

    def extract_field(self, prompt, field_name):
        match = re.search(rf"{field_name} is (.+)", prompt, re.IGNORECASE)
        return match.group(1).strip().replace("'", "''") if match else None

    def sanitize_query(self, query):
        query = query.strip()
        query = '\n'.join([line for line in query.split('\n') if not line.strip().startswith('--')])
        statements = query.split(';')
        return statements[0].strip()  # Return the first statement only

    def execute_sql_query(self, sql_query):
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql_query)
                rows = cursor.fetchall()

                if not rows:
                    return {"message": "No results found"}

                column_names = [desc[0] for desc in cursor.description]
                result = [dict(zip(column_names, row)) for row in rows]

                return result
        except Exception as e:
            raise Exception(f"SQL execution error: {str(e)}")

class GenerateSQLSalesTable(APIView):
            def post(self, request):
                serializer = QuerySerializer(data=request.data)
                if serializer.is_valid():
                    prompt = serializer.validated_data['text']
                    try:
                        # Generate the SQL query
                        generated_sql = self.generate_sql_query_for_purchase(prompt)

                        if not generated_sql:
                            return Response({'error': 'Generated SQL query is empty.'},
                                            status=status.HTTP_400_BAD_REQUEST)

                        # Execute the generated SQL query and get results
                        result = self.execute_sql_query(generated_sql)

                        return Response({'sql_query': generated_sql, 'results': result}, status=status.HTTP_200_OK)
                    except Exception as e:
                        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            def generate_sql_query_for_purchase(self, prompt):
                tokenizer = AutoTokenizer.from_pretrained("NumbersStation/nsql-350M")
                model = AutoModelForCausalLM.from_pretrained("NumbersStation/nsql-350M")


                text = f"""
                -- Using valid SQLite, answer the following question based on the below table structure :
              
                -- Table name: project_sales
                -- Columns: sales_id (INTEGER PRIMARY KEY), customer_id (INTEGER FOREIGN KEY), item_id (INTEGER FOREIGN KEY), quantity (INTEGER), total_price (DECIMAL), sales_date (DATE)
                
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
                    with connection.cursor() as cursor:
                        cursor.execute(sql_query)
                        rows = cursor.fetchall()

                        if not rows:
                            return {"message": "No results found"}

                        # Optionally, get column names
                        column_names = [desc[0] for desc in cursor.description]

                        # Format the result in a list of dictionaries
                        result = [dict(zip(column_names, row)) for row in rows]

                        return result
                except Exception as e:
                    # Handle SQL errors or other exceptions
                    raise Exception(f"SQL execution error: {str(e)}")


class GenerateSQLPurchaseTable(APIView):
    def post(self, request):
        serializer = QuerySerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data['text']
            try:
                # Generate the SQL query
                generated_sql = self.generate_sql_query_for_purchase(prompt)

                if not generated_sql:
                    return Response({'error': 'Generated SQL query is empty.'},
                                    status=status.HTTP_400_BAD_REQUEST)

                # Execute the generated SQL query and get results
                result = self.execute_sql_query(generated_sql)

                return Response({'sql_query': generated_sql, 'results': result}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def generate_sql_query_for_purchase(self, prompt):
        tokenizer = AutoTokenizer.from_pretrained("NumbersStation/nsql-350M")
        model = AutoModelForCausalLM.from_pretrained("NumbersStation/nsql-350M")


        text = f"""
                -- Using valid SQLite, answer the following question based on the table structure below:

                -- Table name: project_purchase 
                -- Columns: item_id (INTEGER PRIMARY KEY), purchase_date (DATE), name (TEXT), quantity (INTEGER), price (DECIMAL)

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
            with connection.cursor() as cursor:
                cursor.execute(sql_query)
                rows = cursor.fetchall()

                if not rows:
                    return {"message": "No results found"}

                # Optionally, get column names
                column_names = [desc[0] for desc in cursor.description]

                # Format the result in a list of dictionaries
                result = [dict(zip(column_names, row)) for row in rows]

                return result
        except Exception as e:
            # Handle SQL errors or other exceptions
            raise Exception(f"SQL execution error: {str(e)}")

class GenerateSQLCustomerTable(APIView):
            def post(self, request):
                serializer = QuerySerializer(data=request.data)
                if serializer.is_valid():
                    prompt = serializer.validated_data['text']
                    try:
                        # Generate the SQL query
                        generated_sql = self.generate_sql_query_for_purchase(prompt)

                        if not generated_sql:
                            return Response({'error': 'Generated SQL query is empty.'},
                                            status=status.HTTP_400_BAD_REQUEST)

                        # Execute the generated SQL query and get results
                        result = self.execute_sql_query(generated_sql)

                        return Response({'sql_query': generated_sql, 'results': result}, status=status.HTTP_200_OK)
                    except Exception as e:
                        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            def generate_sql_query_for_purchase(self, prompt):
                tokenizer = AutoTokenizer.from_pretrained("NumbersStation/nsql-350M")
                model = AutoModelForCausalLM.from_pretrained("NumbersStation/nsql-350M")

                if 'customer' or 'customers' in prompt:
                    prompt = prompt.replace("customer", "project_customer")

                text = f"""
                -- Using valid SQLite, answer the following question based on the below table structure :

                 -- Table name: project_customer 
                -- Columns: customer_id (INTEGER PRIMARY KEY), customer_name (TEXT), customer_email (TEXT UNIQUE), phone_number (TEXT)

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
                    with connection.cursor() as cursor:
                        cursor.execute(sql_query)
                        rows = cursor.fetchall()

                        if not rows:
                            return {"message": "No results found"}

                        # Optionally, get column names
                        column_names = [desc[0] for desc in cursor.description]

                        # Format the result in a list of dictionaries
                        result = [dict(zip(column_names, row)) for row in rows]

                        return result
                except Exception as e:
                    # Handle SQL errors or other exceptions
                    raise Exception(f"SQL execution error: {str(e)}")

