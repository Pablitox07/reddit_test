
// create a function to publish the comment
function publish_comment (){
    const comment_text_input = document.getElementById("post_comment_button");
    const user = JSON.parse(localStorage.getItem("user_info"));
    const user_info_login = document.getElementById("user_info_login");

    if (comment_text_input.value == "" || comment_text_input.value == null){
        user_info_login.innerHTML = `<h3 class="create_post_text">Comment cannot be empty</h3><img src="../static/failed_face.jpg" alt="" srcset="" class="failed_face">`;
    }
    user_info_login.innerHTML = ``;

    const params = {post_id: received_post_id, comment_author: user["user_id"], comment_text: comment_text_input.value};
    fetch(`${website}/post_comment`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}`,
        "Content-Type": "application/json", },
        body: JSON.stringify(params)
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        if (data["status"] == 401) {
            localStorage.setItem("user_info", "");
            localStorage.setItem("authToken", "");
            window.location.href = `${website}/login`; 
        }
        else if (data["status"] >= 400){
            const user_info_login = document.getElementById("user_info_login");
            user_info_login.innerHTML = `<h3 class="create_post_text">${data["message"]}</h3><img src="../static/failed_face.jpg" alt="" srcset="" class="failed_face">`;
        }
        else {
            document.getElementById("post_comment_button").value = "";
            location.reload();
        }
    })
    .catch(error => {
        console.log(error);
    });
}

// this loads the comments if there are 
function load_comments(post_id, current_user_id){
    fetch(`${website}/load_comments?post_id=${post_id}&current_user_id=${current_user_id}`, {
        method: "GET"
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        for (const key in data["list_comments_posts"]) {
            const comment_id = data["list_comments_posts"][key]["comment_id"];
            const profile_pic = `${website}/static/${data["list_comments_posts"][key]["profile_picture"]}`;
            const username = data["list_comments_posts"][key]["username"];
            const user_id = data["list_comments_posts"][key]["user_id"];
            const comment_text = data["list_comments_posts"][key]["comment_text"];
            const number_likes = data["list_comments_posts"][key]["number_likes"];
            let like_status = '';
            let dislike_status = '';

            if (data["list_comments_posts"][key]["liked_dislike_status"] == 'l'){
                like_status = 'button_liked';
                dislike_status = 'button_icon_dislike';
            }
            else if (data["list_comments_posts"][key]["liked_dislike_status"] == 'd'){
                dislike_status = 'button_disliked';
                like_status = 'button_icon_like';
            }
            else if (data["list_comments_posts"][key]["liked_dislike_status"] == 'n') {
                dislike_status = 'button_icon_dislike';
                like_status = 'button_icon_like';
            }
            const new_comment_div = document.createElement("div");
            new_comment_div.innerHTML = `
            <div class="div_comment">
                <div class="post_div" style="max-height:initial;">
                    <div class="post_user_info">
                        <img src="${profile_pic}" class="user_icon_profile">
                        <a class="top_user_name" href="${website}/profile/${user_id}">${username}</a>
                    </div>
                    <span class="post_text">${comment_text}</span>
                    <div class="div_icons_posts">
                        <div class="icon_container">
                            <button class="button_like_dislike_no_like_dislike" onclick="like_or_dislike (${comment_id}, 'like', 'comment');">
                                <svg class="${like_status}" id="like_icon_comment_id_${comment_id}" fill="currentColor" height="16" width="16" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M10 19c-.072 0-.145 0-.218-.006A4.1 4.1 0 0 1 6 14.816V11H2.862a1.751 1.751 0 0 1-1.234-2.993L9.41.28a.836.836 0 0 1 1.18 0l7.782 7.727A1.751 1.751 0 0 1 17.139 11H14v3.882a4.134 4.134 0 0 1-.854 2.592A3.99 3.99 0 0 1 10 19Zm0-17.193L2.685 9.071a.251.251 0 0 0 .177.429H7.5v5.316A2.63 2.63 0 0 0 9.864 17.5a2.441 2.441 0 0 0 1.856-.682A2.478 2.478 0 0 0 12.5 15V9.5h4.639a.25.25 0 0 0 .176-.429L10 1.807Z"></path>
                                </svg>
                            </button>
                            <span id="number_likes_comment_${comment_id}" class="post_name_url">${number_likes}</span>
                            <button class="button_like_dislike_no_like_dislike" onclick="like_or_dislike (${comment_id}, 'dislike', 'comment');">
                                <svg class="${dislike_status}" id="dislike_icon_comment_id_${comment_id}" fill="currentColor" height="16" width="16" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M10 1c.072 0 .145 0 .218.006A4.1 4.1 0 0 1 14 5.184V9h3.138a1.751 1.751 0 0 1 1.234 2.993L10.59 19.72a.836.836 0 0 1-1.18 0l-7.782-7.727A1.751 1.751 0 0 1 2.861 9H6V5.118a4.134 4.134 0 0 1 .854-2.592A3.99 3.99 0 0 1 10 1Zm0 17.193 7.315-7.264a.251.251 0 0 0-.177-.429H12.5V5.184A2.631 2.631 0 0 0 10.136 2.5a2.441 2.441 0 0 0-1.856.682A2.478 2.478 0 0 0 7.5 5v5.5H2.861a.251.251 0 0 0-.176.429L10 18.193Z"></path>
                                </svg>
                            </button>
                        </div>
                    </div>            
                </div>
            </div>`;
            document.getElementById("div_comments").appendChild(new_comment_div);
        }
    })   
}

// funtion to like and dislike comments 
function like_or_dislike(comment_or_post_id, like_or_dislike, post_or_comment) {
    // Check the comment_id that the button was pressed for
    if (user_info["user_info"] == null){
        window.location.href = `${website}/login`;
    }
    try {
        const params = {
            comment_or_post_id: comment_or_post_id,
            like_or_dislike: like_or_dislike,
            user_id: user_info["user_info"]["user_id"],
            post_or_comment: post_or_comment
        };

        fetch(`${website}/post_like_dislike`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("authToken")}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify(params),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data["status"] === 401) {
                    // Unauthorized: Redirect to login
                    localStorage.setItem("user_info", "");
                    localStorage.setItem("authToken", "");
                    window.location.href = `${website}/login`;
                } else if (data["status"] >= 400) {
                    // Display error message
                    user_info_login.innerHTML = `
                        <h3 class="create_post_text">${data["message"]}</h3>
                        <img src="../static/failed_face.jpg" alt="" class="failed_face">
                    `;
                } else {
                    // Update the like/dislike status
                    if (data["change_status"]) {
                        const span_number_likes = document.getElementById(`number_likes_${post_or_comment}_${comment_or_post_id}`);
                        if (like_or_dislike === "like") {
                            // Increment like count and update colors
                            span_number_likes.innerHTML = data["number_likes"];
                            document.getElementById(`like_icon_${post_or_comment}_id_${comment_or_post_id}`).style.color = "green";
                            document.getElementById(`dislike_icon_${post_or_comment}_id_${comment_or_post_id}`).style.color = "black";
                        } else {
                            // Decrement like count and update colors
                            span_number_likes.innerHTML = data["number_likes"];
                            document.getElementById(`like_icon_${post_or_comment}_id_${comment_or_post_id}`).style.color = "black";
                            document.getElementById(`dislike_icon_${post_or_comment}_id_${comment_or_post_id}`).style.color = "red";
                        }
                    }
                }
            })
    } 
    catch (error) {
        if ("TypeError: user_info is null" == error){
            window.location.href = `${website}/login`;
        }
    }
}


// -------------------------- after page is loaded -------------------------
document.addEventListener("DOMContentLoaded", ()=> {
    if (user_info["user_info"] == null || user_info["user_auth"] == null ) {
        document.getElementById("comment_input_show_input").innerHTML = '<a href="/login" class="login_if_user_not_logged">Login to comment</a>';
    }
    let fetch_url; 
    if (user_info["user_logged"]){
        let user_id = user_info['user_info']['user_id'];
        fetch_url = `${website}/get_post_info?post_id=${received_post_id}&user_id=${user_id}`;
    }
    else{
        fetch_url = `${website}/get_post_info?post_id=${received_post_id}&user_id=nouser`;
    }
    fetch(fetch_url, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
        }
        })
        .then(response => {
            return response.json();
        })
        .then(data => {
            if (data["status"] >= 400){
                document.getElementById("main_div_post").innerHTML = `<h3 class="create_post_text">${data["message"]}</h3><img src="../static/failed_face.jpg" alt="" srcset="" class="failed_face">`;
            }
            else {
                document.title = data["title"];
                document.getElementById("post_title_h1").innerHTML = data["title"];
                document.getElementById("post_author").innerHTML = data["username"];
                document.getElementById("post_author").href = `${website}/profile/${data["user_id"]}`;
                document.getElementById("author_profile_picture").src = `${website}/static/${data["author_profile_picture"]}`;
                document.getElementById("post_content_span").innerHTML = data["content"];
                document.getElementById(`number_likes_post_${received_post_id}`).innerHTML = data["number_likes"];
                document.getElementById("category_post_span").innerHTML = `CATEGORY: ${data["category"]}`;
                if (data["post_like_status"] == "d"){
                    document.getElementById(`dislike_icon_post_id_${received_post_id}`).style.color = "red";
                }
                else if (data["post_like_status"] == "l"){
                    document.getElementById(`like_icon_post_id_${received_post_id}`).style.color = "green";
                }
    
                // if there are not comments a message will appear telling the user that
                if (data["number_comments"] == 0){
                    const no_comments_message = document.createElement("div");
                    no_comments_message.innerHTML = `<h3 class="create_post_text">No comments yet</h3><img src="../static/failed_face.jpg" alt="" srcset="" class="failed_face">`;
                    document.getElementById("div_comments").appendChild(no_comments_message);
                }
                
                // if there are comments then it should load the comments
                else{
                    if (user_info["user_logged"]) {
                        load_comments(received_post_id, user_info["user_info"]["user_id"]); 
                    }
                    else {
                        load_comments(received_post_id, "not_logged"); 
                    }
                }
            }
        })
});