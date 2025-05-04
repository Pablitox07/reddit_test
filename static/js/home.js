
document.addEventListener("DOMContentLoaded", ()=> {
    // fetch request to get the latest 10 posts from the DB 
    fetch(`/load_home_posts`)
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        let all_posts = "";
        for (const key in data) {
            let color_likes = "";
            if (parseInt(data[key]["number_likes"]) == 0){
                color_likes = "white";
            }
            else if (parseInt(data[key]["number_likes"]) > 0) {
                color_likes = "green";
            }
            else {
                color_likes = "red";
            }
            all_posts += `<div class="post_div">
                <div class="post_user_info">
                    <img src="/static/images/${data[key]["profile_pic"]}" class="user_icon_profile">
                    <a class="top_user_name" href="/profile/${data[key]["user_id"]}">${data[key]["username"]}</a>
                </div>
                <a href="/posts/${data[key]["post_id"]}" class="post_name_url">${data[key]["tittle"]}</a>
                <a href="/posts/${data[key]["post_id"]}" class="post_text">${data[key]["post_text"]}</a>
                <div class="div_icons_posts">
                    <div class="icon_container">
                        <a href="/posts/${data[key]["post_id"]}" class="post_name_url" style="color: ${color_likes};">${data[key]["number_likes"]}</a>
                    </div>
                    <div class="icon_container">
                        <a href="/posts/${data[key]["post_id"]}" >
                        <div class="comments_div">
                            
                            <svg rpl="" aria-hidden="true" fill="currentColor" height="20" icon-name="comment-outline" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" class="comments_logo">
                                <path d="M10 19H1.871a.886.886 0 0 1-.798-.52.886.886 0 0 1 .158-.941L3.1 15.771A9 9 0 1 1 10 19Zm-6.549-1.5H10a7.5 7.5 0 1 0-5.323-2.219l.54.545L3.451 17.5Z"></path>
                            </svg>
                            <span class="post_name_url">${data[key]["number_comments"]}</span>
                        </div>
                        </a>
                    </div>
                </div>            
            </div>`;

            document.getElementById("div_posts").innerHTML = all_posts;
        } 
    })
    .catch(error => {
        console.error('There was a problem with the fetch operation:', error);
    });

    // this part loads the list of categories. this list of categories is still hard coded.
    const list_categories = ["General Discussions", "Technical Support", "Community Projects and Collaboration", "Development and Coding", "Design and Creativity", "Career and Professional Development", "Learning and Resources", "Feedback and Suggestions", "Special Interest Groups", "Events and Meetups", "Gaming and Entertainment", "Marketplace and Classifieds", "Health and Wellness", "Sports", "Travel and Adventure", "Food and Cooking", "Parenting and Family", "Hobbies and Crafts", "Science and Technology", "News and Current Events"];
    const list_elements_div_html = document.getElementById("div_list_categories");
    let final_list_categories = `<span class="mini_header_text">CATEGORIES</span>`;
    list_categories.forEach(Element =>{
        const category_name_without_spaces = Element.replace(/ /g, "_");
        final_list_categories += `<a href="/categories/${category_name_without_spaces}" class="category_link_name">&middot; ${Element}</a> `;
    });

    list_elements_div_html.innerHTML = final_list_categories;

    fetch(`/load_top_post`)
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log(data);
        let top_posters = "";
        let top_posts = ""; 
        for (const key in data["top_posters"]) {
            console.log(key);
            top_posters += `<div class="div_top_user_info"><img src="/static/images/${data["top_posters"][key]["profile_pic"]}" class="user_icon_profile"><a class="top_user_name" href="/profile/${data["top_posters"][key]["user_id"]}">&middot; ${data["top_posters"][key]["username"]} &middot; ${data["top_posters"][key]["user_score"]} Posts</a></div>`;
            top_posts += `<div class="div_top_user_info"><img src="/static/images/${data["top_posts"][key]["profile_pic"]}" class="user_icon_profile"><a href="/posts/${data["top_posts"][key]["post_id"]}" class="top_user_name">${data["top_posts"][key]["tittle"]}</a></div>`
        }
        document.getElementById("list_top_users").innerHTML = top_posters;
        document.getElementById("top_posts_list").innerHTML = top_posts;
    })

});