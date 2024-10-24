import React from "react";
import "../Styles/header.css";
import { Link } from 'react-router-dom';

function Header() {
  return (
    <>
      <div className="header">
        <div className="title">Inventory Insights</div>
        <ul class="navbar-nav me-auto mb-2 mb-lg-0" className="navbar">
          <li class="nav-item">
             <Link to="/" className="navitems">Home</Link>
          </li>

          <li class="nav-item">
             <Link to="/sales" className="navitems">Sales Info</Link>
          </li>

          <li class="nav-item">
             <Link to="/customer" className="navitems">Customer Info</Link>
          </li>

          <li class="nav-item">
             <Link to="/purchase" className="navitems">Purchase Info</Link>
          </li>

          <li class="nav-item">
             <Link to="/allinfo" className="navitems">All Info</Link>
          </li>


           
        </ul>
      </div>
    </>
  );
}

export default Header;
