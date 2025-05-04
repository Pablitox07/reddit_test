//const website = "http://127.0.0.1:5000";

function check_empty_inputs (items_to_check, user_info_login) {
    let information_needed = true; 
    items_to_check.forEach(Element =>{
        if (Element.value == ""){
            Element.style.border = "1px solid red";
            information_needed = false;
            user_info_login.innerHTML = `<h3 class="create_post_text">All fills must be filled.</h3><img src="/static/images/failed_face.jpg" alt="" srcset="" class="failed_face">`;
        }
        else {
            Element.style.border = "0px";
        }
    });
    if (information_needed){
        user_info_login.innerHTML = "";
    }
    return information_needed;
}

if (localStorage.getItem("authToken") == null || localStorage.getItem("authToken") == "") {
    window.location.href = `/login`; 
}

document.addEventListener("DOMContentLoaded", ()=> {
    const list_categories = ["General Discussions", "Technical Support", "Community Projects and Collaboration", "Development and Coding", "Design and Creativity", "Career and Professional Development", "Learning and Resources", "Feedback and Suggestions", "Special Interest Groups", "Events and Meetups", "Gaming and Entertainment", "Marketplace and Classifieds", "Health and Wellness", "Sports", "Travel and Adventure", "Food and Cooking", "Parenting and Family", "Hobbies and Crafts", "Science and Technology", "News and Current Events"];
    const options_html_element = document.getElementById("categories_dropdown");
    const button_publish_post = document.getElementById("button_publish_post");
    const user_info_login = document.getElementById("user_info_login");

    list_categories.forEach(Element =>{
        const new_option = document.createElement("option");

        new_option.text = Element;
        new_option.value = Element;

        options_html_element.add(new_option);
    });

    button_publish_post.addEventListener("click", ()=> {
        let check_empty_inputs_result = false;
        const tittle_input = document.getElementById("post_tittle");
        const options_html_element = document.getElementById("categories_dropdown");
        // get the text of the quill editor and checks if it is empty or not.  
        if (quill.getText().trim() == "") {
            quill.root.style.border = "1px solid red";
            user_info_login.innerHTML = `<h3 class="create_post_text">All fills must be filled.</h3><img src="/static/images/failed_face.jpg" alt="" srcset="" class="failed_face">`;
        }
        else {
            quill.root.style.border = "0px";
            user_info_login.innerHTML = "";
            check_empty_inputs_result = check_empty_inputs([tittle_input, options_html_element], user_info_login); 
        }

        // If everything then proceed to post the user post 
        if (check_empty_inputs_result) {
            const user = JSON.parse(localStorage.getItem("user_info"));
            const params = {userid: user["user_id"], title: tittle_input.value, text: quill.root.innerHTML, category: options_html_element.value};

            fetch(`${website}/publishPost`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}`,
                            "Content-Type": "application/json", },
                            body: JSON.stringify(params)
            }).then(response => {
                    return response.json();
            }).then(data => {
                window.location.href = `/posts/${data["post_id"]}`;
            }).catch(error => console.error("Error:", error));
        }
    });
});