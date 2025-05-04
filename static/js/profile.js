// try catch to check if the user trying to access the profile is the same as the logged user. 
// if the user accessinig the profile is the same as the user logged it should give the user the hability to modify some aspects of the profile. 
// if the user is different then they should only be able to see user information
try {
    if (received_user_id == JSON.parse(localStorage.getItem("user_info"))["user_id"]){
        document.getElementById("div_change_profile_pic").style.display = "flex";
    }
} 
catch (error) {
    console.error("An error occurred:", error.message);
} 
  

const button_change_password = document.getElementById("button_change_profile_pic");

button_change_password.addEventListener('click', function() {
    const file_profile = document.getElementById("imageUpload"); 
    if (file_profile.files.length > 0) {
        const profile_pic_file = file_profile.files[0];
        const formData = new FormData();
        formData.append('file', profile_pic_file);

        fetch(`${website}/change_profile_pic?user=${received_user_id}`, {
            method: 'POST',
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("authToken")}`
            },
            body: formData
        })
        .then(response => {
            if (response.status == 401){
                window.location.href = "/login"
            }
            return response.json();
        })
        .then(data => {
            const user_info = JSON.parse(localStorage.getItem("user_info"));
            user_info["profile_pic"] = data["message"];
            localStorage.setItem("user_info", JSON.stringify(user_info));
            location.reload();
        })
    } 
    else {
        message.textContent = 'No file selected!';
    }
});

fetch(`${website}/get_user_info?user=${received_user_id}`)
.then(response => {
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    return response.json();
})
.then(data => {
    console.log(data);
    document.title = `${data["username"]}'s profile`;
    document.getElementById("span_show_username").innerHTML = `${data["username"]}'s profile`;
    document.getElementById("profile_pic_user_profile").src = `/static/images/${data["profile_pic"]}`;
    document.getElementById("joined_on_span").innerHTML = `Joined on: ${data["joined_on"]}`;
    document.getElementById("first_post_span").innerHTML = `First Post:  ${data["first_post_title"]}`;
    document.getElementById("latest_post_span").innerHTML = `Latest Post: ${data["latest_post_title"]}`;
    document.getElementById("popular_post_span").innerHTML = `Most popular post: ${data["popular_post_title"]}`
})
