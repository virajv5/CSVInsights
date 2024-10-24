import React from "react";
import { Routes, Route, BrowserRouter } from "react-router-dom";
import Sales from "./Components/Sales";
import Home from "./Components/Home";
import Customer from "./Components/Customer";
import Purchase from "./Components/Purchase";
import Allinfo from "./Components/Allinfo";





function App() {
  return (
   <BrowserRouter>
   <div>
     <Routes>
       <Route path="/sales" element={<Sales/>}/>
       <Route path="/" element={<Home/>}/>
       <Route path="/customer" element={<Customer/>}/>
       <Route path="/purchase" element={<Purchase/>}/>
       <Route path="/allinfo" element={<Allinfo/>}/>
     </Routes>
   </div>
   </BrowserRouter>
  );
}

export default App;