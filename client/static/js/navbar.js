$(document).ready(function() {
    
    // fetch('https://a4a2-202-51-208-50.ngrok-free.app/login-status', {method: 'POST'})
    fetch('/login-status', {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        credentials: 'same-origin'})
    .then(response => {
        if (!response.ok) {
            throw new Error('Terjadi kesalahan saat mengambil data.');
        }
        return response.json();
    })
    .then(response => {
        
        if (response.logged_in) {
            console.log('Login')
            $('#nav-right').append(`
                <div class="dropdown ms-2 " id="profile-dropdown" >
                    <button class="btn dropdown-toggle btn-outline-custom" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                        <i class="fa-regular fa-user me-2 " aria-disabled="true" style="font-size: 15px;"></i>              
                        ${response.username}
                    </button>
                    <ul class="dropdown-menu no-style" >
                        <li><a class="dropdown-item no-style" href="/account" style="color: black;">Profile</a></li>
                        <li><a class="dropdown-item no-style" href="/riwayat-transaksi" style="color: black;">Riwayat Transaksi</a></li>
                        <li><a class="dropdown-item no-style visually-hidden" href="/dashboard" style="color: black;" id="btn-dashboard">Dashboard</a></li>
                        <hr>
                        <li><a class="dropdown-item no-style" href="/logout" style="color: black;">Keluar<span class="ms-2"><i class="fa-solid fa-right-from-bracket" style="font-size: 15px;"></i></span></a> 
                        </li>
                    </ul>
                </div>
            `)

            if (response.level_user === '1' || response.level_user === '2') {
                $('#btn-dashboard').removeClass('visually-hidden')
            }

            
        } else {
            $('#nav-right').append(`
            <a href="/login" type="button" class="btn btn-outline-custom ms-3">Login</a>
    
            <a href="/register" class="btn custom-btn ms-3">Sign Up</a>
            `)
        }
    })
    .catch(error => {
        
    });



    
});