import React from "react";
import CustomNavbar from "./Header";
import "../Styles/home.css";
import{
  Card,
  CardBody,
  CardText,
} from 'reactstrap'

function Home() {
  return (
    <>
      <CustomNavbar />
      <div className="hcard">

        
         <p className="ctitle"> Table Question <br/> 
          Answering Model </p>


        <Card
          style={{
            width: "25 rem",
          }}  className="details"
        >
          <CardBody>
            <CardText className="CardText">
            Our Table Question Answering Model is purpose-built to simplify inventory management 
            tasks. Upload your CSV files customer, purchase, and sales data in a structured 
            format and ask your questions in natural language. Powered by the 
            "NumbersStation/nsql-350M" model, the system translates your queries into precise 
            SQL commands, executing them in real-time against your database. Get answers to your 
            inventory-related questions
            </CardText>
          </CardBody>
        </Card>
      </div>

      
    </>
  );
}

export default Home;
