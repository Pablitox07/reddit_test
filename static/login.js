const website = "http://127.0.0.1:5000";

function check_empty_fills(list_inputs_html, user_info_login){
    let show_message = true; 
    list_inputs_html.forEach(element => {
        if (element.value === ""){
            element.style.border = "1px solid red";
            show_message = false;
            user_info_login.innerHTML = `<h3 class="create_post_text">All fills must be filled.</h3><img src="../static/failed_face.jpg" alt="" srcset="" class="failed_face">`;
        }
        else {
            element.style.border = "0px";
        }
    });
    if (show_message){
        user_info_login.innerHTML = "";
    }
    return show_message;
}

document.addEventListener("DOMContentLoaded", ()=> {
    const login_button = document.getElementById("login_button");

    // executes when user click the login button
    login_button.addEventListener("click", ()=>{
        // get the username, password and message div
        const username = document.getElementById("username");
        const password = document.getElementById("password");
        const user_info_login = document.getElementById("user_info_login");

        // checks if there are empty spaces and if there are it will show the user which
        if (check_empty_fills([username, password], user_info_login)) {
            const params = {username_email: username.value, password: password.value};
            fetch(`${website}/loguser`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(params),
            })
            .then(response => {
                return response.json();
            })
            .then(data => {
                if (data["status"] >= 400){
                    user_info_login.innerHTML = `<h3 class="create_post_text">${data["message"]}</h3><img src="../static/failed_face.jpg" alt="" srcset="" class="failed_face">`;
                }
                else {
                    localStorage.setItem("authToken", data["token"]);
                    localStorage.setItem("user_info",JSON.stringify(data["user_info"]));

                    window.location.href = `${website}/`; 
                }
            })
            .catch(error => {
                console.log(error);
            });
        }
        
    });
});