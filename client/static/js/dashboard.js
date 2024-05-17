$(document).ready(function () {
    check_permission()
    // $('#nama-user').append('Samantha Doe')
});

function check_permission() {
    fetch('http://127.0.0.1:5000/login-status', {method: 'post'})
    // fetch('https://a4a2-202-51-208-50.ngrok-free.app/login-status', {method: 'post'})
    .then(response => response.json())
    .then(response => {
        fetch(`http://127.0.0.1:4000/get-profile-image/${response.user_id}`, {method: 'post'})
        .then(response => response.json())
        .then(response => {
            $('.avatar-initial').attr('src', `/static/images/profile_image/${response}`);
        })

        $('#nama-user').append(response.nama)
        

        let container = $('#manage-account')

        if (response.level_user === '1') {
            $('#manage-account').removeClass('visually-hidden')
            $('#add-carousel').removeClass('visually-hidden')
            $('.movie-add').removeClass('visually-hidden')
            $('#tile-user').append('Super Admin')
        } 
        else {
            $('#tile-user').append('Admin')
        }

    })
    .catch(error => {
        console.log(error)
    })
}

// function profile () {
//     fetch('http://127.0.0.1:5000/login-status')
// }

function getCurrentTime() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}


let formatDate = (tanggal) => {
    let date = new Date(tanggal);
    return `${date.getDate(tanggal)}-${date.getMonth()+1}-${date.getFullYear()}`
}

let dateToday = () => {
    let date = new Date();
    return `${date.getDate()}-${date.getMonth()+1}-${date.getFullYear()}`
}

const formatRupiah = (amount) => {
    return amount.toLocaleString('id-ID', { style: 'currency', currency: 'IDR' });
};

const formatingRupiah = (amount) => {
    amount = Math.floor(amount);
    return "Rp" + amount.toLocaleString('id-ID');
};
