const website = "http://127.0.0.1:5000";


function border_red_not(element) {
    if (element.value === ""){
        element.style.border = "1px solid red";
    }
    else{
        element.style.border = "0px";
    }
}

function something_wrong_inputs (email_string, username_string, password_1, password_2){
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const noSpaceRegex = /^\S+$/;
    if (!emailRegex.test(email_string)){
        return {"result": true, "message": "The format of the email is incorrect."};
    }
    else if (!noSpaceRegex.test(username_string)){
        return {"result": true, "message": "username cannot contain spaces."};
    }
    else if (username_string.length < 3){
        return {"result": true, "message": "username cannot be less than 3 characters."};
    }
    else if (username_string.length > 15){
        return {"result": true, "message": "username cannot have more than 15 characters."};
    }
    else if (password_1 != password_2){
        return {"result": true, "message": "The password must be the same."};
    }
    else if (password_1.length < 8){
        return {"result": true, "message": "The password must be at least 8 characters long."};
    }
    else {
        return {"result": false, "message": "correct"};
    }
}

document.addEventListener("DOMContentLoaded", ()=> {
    const register_button = document.getElementById("register_button");

    register_button.addEventListener("click", ()=> {
        // HTML inputs 
        const username = document.getElementById("username");
        const email = document.getElementById("email");
        const password_1 = document.getElementById("password_1");
        const password_2 = document.getElementById("password_2");

        // gets the div where usewr will see info about the registration
        let failed_message = document.getElementById("failed_message");

        // shows which inputs must be filled by turning them red 
        list_inputs = [username, email, password_1, password_2];
        list_inputs.forEach(element => {
            border_red_not(element);
        });

        const results_something_wrong_inputs = something_wrong_inputs(email.value, username.value, password_1.value, password_2.value);
        
        if (username.value === "" || email.value === "" || password_1.value === "" || password_2.value === ""){
            failed_message.innerHTML = '<h3 class="create_post_text">All fills must be filled.</h3><img src="../static/failed_face.jpg" alt="" srcset="" class="failed_face">';
        }
        else if (results_something_wrong_inputs["result"]){
            failed_message.innerHTML = `<h3 class="create_post_text">${results_something_wrong_inputs["message"]}</h3><img src="../static/failed_face.jpg" alt="" srcset="" class="failed_face">`;
        }



        // EXECUTE ONLY IF EVERYTHING ELSE IS CORECT 
        else {
            failed_message.innerHTML = "";
            const params = { email: email.value, username: username.value, password_1: password_1.value };

            fetch(`${website}/registerUser`, {
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
                        failed_message.innerHTML = `<h3 class="create_post_text">${data["message"]}</h3><img src="../static/failed_face.jpg" alt="" srcset="" class="failed_face">`;
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
