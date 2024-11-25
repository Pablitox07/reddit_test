document.addEventListener("DOMContentLoaded", ()=> {
    // this part loads the list of categories. this list of categories is still hard coded.
    const list_categories = ["General Discussions", "Technical Support", "Community Projects and Collaboration", "Development and Coding", "Design and Creativity", "Career and Professional Development", "Learning and Resources", "Feedback and Suggestions", "Special Interest Groups", "Events and Meetups", "Gaming and Entertainment", "Marketplace and Classifieds", "Health and Wellness", "Sports", "Travel and Adventure", "Food and Cooking", "Parenting and Family", "Hobbies and Crafts", "Science and Technology", "News and Current Events"];
    const list_elements_div_html = document.getElementById("div_list_categories");
    let final_list_categories = `<span class="mini_header_text">CATEGORIES</span>`;
    list_categories.forEach(Element =>{
        const category_name_without_spaces = Element.replace(/ /g, "_");
        final_list_categories += `<a href="/categories/${category_name_without_spaces}" class="category_link_name">&middot; ${Element}</a> `;
    });

    list_elements_div_html.innerHTML = final_list_categories;

});