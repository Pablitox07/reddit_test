// Person.js
export default class User {
    constructor(email, profile_pic, user_id, username) {
        this.email = email;
        this.profile_pic = profile_pic;
        this.user_id = user_id;
        this.username = username;
    }

    greet() {
        console.log(`Hi, my name is ${this.username}.`);
    }
}

