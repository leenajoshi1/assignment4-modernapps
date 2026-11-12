import {Routes, Route} from "react-router-dom";
import './App.css';
import GeneralUser from "./components/GeneralUser";
import Admin from "./components/Admin";
import Navbar from "./components/Navbar";
import PhotoPortal from "./components/PhotoPortal";
export default function App() {
  return <Routes>
    <Route path="/" element={<GeneralUser/>}/>
    <Route path="/admin" element={<Admin/>}/>
    <Route path="/photo-portal" element={<><Navbar/><PhotoPortal/></>}/>
  </Routes>;
}
