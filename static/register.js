document.addEventListener("DOMContentLoaded", ()=> {
    const register_button = document.getElementById("register_button");

    register_button.addEventListener("click", ()=> {
        const username = document.getElementById("username");
        const email = document.getElementById("email");
        const password_1 = document.getElementById("password_1");
        const password_2 = document.getElementById("password_2");

        if (username.value === "" || email.value === "" || password_1.value === "" || password_2.value === ""){
            let failed_message = document.getElementById("failed_message");
            failed_message.innerHTML = '<h3 class="create_post_text">All fills must be filled.</h3><img src="../static/failed_face.jpg" alt="" srcset="" class="failed_face">';
        }
        else {
            
        }
    });
});
