import { useState } from "react";
import { useNavigate } from "react-router-dom";


export default function Admin() {

   const [name, setName] = useState("");
   const [password, setPassword] = useState("");
   const [userFound, setUserFound] = useState(true);
   const navigate = useNavigate();

   const handleSubmit = async (e) => {
     e.preventDefault();
     setUserFound(true);
     try {
       const response = await fetch("/api/adminlogin", {
         method: "POST", credentials: "include",
         headers: {"Content-Type": "application/json"},
         body: JSON.stringify({username: name, password}),
       });
       const data = await response.json();
       if (!response.ok || data.message !== "Success") {
         setUserFound(false);
         return;
       }
       localStorage.setItem("name", data.username);
       localStorage.setItem("usertype", data.usertype);
       navigate("/photo-portal");
     } catch (error) {setUserFound(false);}
   };

  return (
    <div>

          <div className="centered">
          <img
                  src="/images/longhorn.png"
                  className="rounded mx-auto d-block"
                  style={{ width: "300px", height: "150px", justifyContent: "center"  }}
                  alt="Longhorn"
          />
          </div>

          <div>
                <div className="centered"><h5>Photo Portal Admin</h5></div>
                <br/>
	        {!userFound && (
	        <div role="alert" className="centered" style={{ color: "red", marginTop: "10px" }}> {name} not found.    </div>
		)}
                <div className="centered">
                <form onSubmit={handleSubmit} action="login" method="post">
                        <input type="text" aria-label="Username" name="username" placeholder="Username" value={name} style={{display: "block" }}  onChange={(e) => setName(e.target.value)} required/>
	                <br/>
                        <input aria-label="Password" type="password" name="password" placeholder="Password" value={password} style={{display: "block" }} 
	                onChange={(e) => setPassword(e.target.value)}
	  	        required/>
	                <br/>
                        <div className="centered"> <button type="submit" className="btn btn-primary">Login</button> </div>
                </form>
                </div>
          </div>

          <div className="centered"><h6><a href="https://www.cs.utexas.edu/~devdatta">Contact us</a></h6></div>
     </div>
  );
}
