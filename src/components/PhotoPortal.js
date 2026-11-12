import React, { useRef, useState, useEffect, useCallback } from "react";
import {useNavigate} from "react-router-dom";

const PhotoPortal = () => {
  const [searchType, setSearchType] = useState("Name");
  const [searchInput, setSearchInput] = useState("");
  const [photoList, setPhotoList] = useState([]);
  const [photoUploadStatus, setPhotoUploadStatus] = useState("");
  const [adminUser, setAdminUser] = useState(false);
  const navigate = useNavigate();
  const commentsRequest = useRef(0);
  const modalRef = useRef();
  const [photoName, setPhotoName] = useState(null);
  const [photoComments, setPhotoComments] = useState(null);
  
  const openModal = (name) => {
     setPhotoName(name);
     setPhotoComments("Loading comments…");
	  

     // Requirement 3.6 Retrieve photo comments from the backend  	  
     fetchPhotoComments(name);

     window.jQuery(modalRef.current).modal("show");
  };

  // ----------------------------------------------------------------------
  // Fetch existing photos on component load
  // ----------------------------------------------------------------------
  const fetchPhotos = useCallback(async () => {
    try {
      const response = await fetch("/api/photos", {credentials: "include"});
      if (!response.ok) {
        throw new Error("Failed to fetch photos");
      }
      const data = await response.json();
      setPhotoList(data.photos); // backend should return {"photos": [...]}
    } catch (error) {
      console.error("Error fetching photos:", error);
      setPhotoUploadStatus("Error loading photo list");
    }
  }, []);

  useEffect(() => {
    let active = true;
    fetch("/api/session", {credentials: "include"}).then(async (response) => {
      if (!response.ok) throw new Error("Login required");
      const user = await response.json();
      if (!active) return;
      setAdminUser(user.usertype === "admin");
      await fetchPhotos();
    }).catch(() => {if (active) navigate("/", {replace: true});});
    return () => {active = false;};
  }, [navigate, fetchPhotos]);


  const fetchPhotoComments = async (name) => {
    const requestId = ++commentsRequest.current;
    try {
      const response = await fetch(`/api/photos/${encodeURIComponent(name)}/comments`, {credentials: "include"});
      if (!response.ok) throw new Error("Unable to load comments");
      const data = await response.json();
      if (requestId === commentsRequest.current) setPhotoComments(data.comments || "No comments added.");
    } catch (error) {
      if (requestId === commentsRequest.current) setPhotoComments(error.message);
    }
  };

  // ----------------------------------------------------------------------
  // Search form submission
  // ----------------------------------------------------------------------
  const handleSearch = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch("/api/search", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: searchType, query: searchInput }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.message || "Search failed");
      setPhotoList(data.results);
    } catch (err) {
      console.error(err);
      setPhotoUploadStatus(err.message);
    }
  };

  // ----------------------------------------------------------------------
  // Upload photo handler
  // ----------------------------------------------------------------------
  const handleUpload = async (e) => {
    e.preventDefault();

    const form = e.currentTarget;
    const formData = new FormData(form);

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        credentials: "include",
        body: formData, // no headers for multipart/form-data
      });

      const data = await response.json();

      if (response.ok) {
        setPhotoUploadStatus(data.message || "Upload successful!");
        await fetchPhotos(); // refresh photo list
        form.reset(); // clear form
      } else {
        setPhotoUploadStatus(data.message || "Upload failed");
      }
    } catch (error) {
      console.error("Error uploading photo:", error);
      setPhotoUploadStatus("Upload failed due to network error");
    }
  };

  const showPhotoDetails = (photo) => {

    console.log("Selected photo:", photo);
    alert("Photo: " + photo.name + " " + photo.date_taken + " " + photo.tags)
  };

  // ----------------------------------------------------------------------
  // Render
  // ----------------------------------------------------------------------
  return (

    <div>
      <div className="modal fade"
        ref={modalRef}
        tabIndex="-1"
        aria-hidden="true"
      >
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">{photoName}</h5>
              <button
                type="button"
                className="close"
                data-dismiss="modal"
                aria-label="Close"
              >×</button>
            </div>
            <div className="modal-body text-center">
              {photoName && (
		<div>
                <img
                  src={`/static/images/photos/${encodeURIComponent(photoName)}`}
                  alt={photoName}
                  style={{ maxWidth: "100%" }}
                />
	        <div style={{whiteSpace: "pre-wrap"}}><h6>Comments</h6>{photoComments}</div>
		</div>
              )}
            </div>
          </div>
        </div>
      </div>

    <div className="container-fluid">
      <div className="row mvh-100 flex-column flex-md-row">
        {/* LEFT PANEL */}
        <div
          className="col-md-2 div_left"
          style={{
            height: "100vh",
            backgroundColor: "lightblue",
          }}
        >
          {/* Search Form */}
          <div className="row">
            <form id="search_form" onSubmit={handleSearch}>
              <label style={{ paddingLeft: "10px" }}>Search</label>
              <select
                id="search_select"
                name="search_select"
                value={searchType}
                onChange={(e) => setSearchType(e.target.value)}
                style={{ marginLeft: "10px" }}
              >
                <option value="Name">Name</option>
                <option value="Date">Date</option>
                <option value="Tags">Tags</option>
              </select>
              <input
                type="text"
                name="search_input"
                id="search_input"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                style={{ marginLeft: "10px" }}
              />
              <button style={{ marginLeft: "10px" }}>Search</button>
            </form>
          </div>

          <hr />

          {/* Photo list */}
          <div className="row">
            <div>
              <ol id="photo_list">
                {photoList.map((photo) => (
                  <li key={photo.name}>
                    <a
                      href={`/static/images/photos/${encodeURIComponent(photo.name)}`}
                      onClick={(e) => {
                        e.preventDefault();
                        showPhotoDetails(photo);
                      }}
                    >
                      {photo.name}
                    </a>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>

        {/* MIDDLE PANEL */}
        <div className="col-md-8 flex-grow-1 div_right" id="entity-form-container">
          <div id="status">
            <div id="status_string" style={{ color: "green" }}>
              {photoUploadStatus}
            </div>
          </div>

	{adminUser && (
          <div id="uploadPhotoFormDiv" style={{ marginTop: "-10px" }}>
            <form id="uploadPhotoForm" onSubmit={handleUpload} encType="multipart/form-data">
              <label>Photo File</label>
              <input
                className="input"
                type="file"
                name="photo_file"
                id="photo_file"
                required
              />
              <br />
              <br />

              <div className="tab1">
                <b style={{ color: "blue" }}>Photo metadata</b>
                <table>
                  <tbody>
                    <tr>
                      <td><label>Date taken</label></td>
                      <td>
                        <input
                          type="date"
                          required
                          name="date_taken"
                          placeholder="YYYY-MM-DD"
                          id="date_taken"
                        />
                      </td>
                    </tr>
                    <tr>
                      <td><label>Tags</label></td>
                      <td>
                        <input
                          type="text"
                          name="tags"
                          placeholder="comma separated tags"
                          id="tags"
                        />
                      </td>
                    </tr>
		    <tr><td><label htmlFor="comments">Comments</label></td><td><textarea name="comments" id="comments" rows="4"/></td></tr>
                  </tbody>
                </table>
                <button className="btn btn-primary">Submit</button>
              </div>
            </form>
          </div>
	)}
        </div>

        {/* RIGHT PANEL */}
        <div
          className="col-md-2 flex-grow-1 div_right"
          id="entity-form-container-2"
          style={{
            height: "100vh",
            backgroundColor: "lightblue",
          }}
        >
          <div className="row">
            <div>
              <h6>Thumbnails:</h6>
              <ol id="available_photos_list">
                {photoList.map((photo) => (
                  <figure key={photo.name}>
                    <li>
                      <img
                        src={`/static/images/photos/${encodeURIComponent(photo.name)}`}
                        height="60"
                        width="60"
                        alt={photo.name}
                        onClick={() => openModal(photo.name)}
                        style={{ cursor: "pointer" }}
                      />
                    </li>
                    <figcaption>{photo.name}</figcaption>
                  </figure>
                ))}
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>

   </div>
  );
};

export default PhotoPortal;

