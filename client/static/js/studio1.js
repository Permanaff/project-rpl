var firstSeatLabel = 1;
let selected_seat = [];
let selected_seat_no = []; 
let price = 0;
let schedule_id;
let tanggal;
let harga;
let jml_seat;
let checkedDrink;
let drink_name;
let user_id;
let movie_title;
let tiket;


const formatRupiah = (amount) => {
    return amount.toLocaleString('id-ID', { style: 'currency', currency: 'IDR' });
};

const seatGui = () => {
  
    let $main = $('#main-body');
      $(`
              <div class="col-2"></div>
              <div class="col">
                  <div class="container d-flex justify-content-center">
                      <div id="seat-map">
                          <div class="front-indicator">Screen</div>
                      </div>
                  </div>
              </div>
              <div class="col-2">
                  <div id="legend"></div>
              </div>
      `).appendTo($main);
  };

   

$(document).ready(function() {
  const urlParams = new URLSearchParams(window.location.search);
  schedule_id = urlParams.get('booking');
  tanggal = urlParams.get('info').split('|')[4];
  harga = parseInt(urlParams.get('info').split('|')[2])+9000;
  jml_seat = urlParams.get('jml_seat');
  schedule_detail()
  drinkList()

  



    let updateButtonStatus = () => {
        const button = $('#confirm-btn');
        if (selected_seat.length === 0 || checkedDrink === undefined || selected_seat.length != jml_seat) {
            button.prop('disabled', true);
        } else {
            button.prop('disabled', false);
        }
    };


    updateButtonStatus()
    seatGui()

var $cart = $('#selected-seats'),
    $counter = $('#counter'),
    $total = $('#total'),
    sc = $('#seat-map').seatCharts({
    map: [
    '__ffffffff_ffffffffff',
    '__ffffffff_ffffffffff',
    '__ffffffff_ffffffffff',
    '__ffffffff_ffffffffff',
    '__ffffffff_ffffffffff',
    'ffffffffff_ffffffffff',
    'ffffffffff_ffffffffff',
    'ffffffffff_ffffffffff',
    'ffffffffff_ffffffffff',
    'fffffffffffffffffffff',
    ],
    seats: {
    f: {
        price   : harga,
        classes : 'regular-class', //your custom CSS class
        category: 'regular-class'
    },      
    
    },
    naming : {
    left : false,
    top : false,
    getLabel : function (character, row, column) {
        var letters = 'KJHGFEDCBA'; 

        var index = row - 1;

        var seatLabelChar = letters[index];


        if (row <=10 && row >=6 && column >= 12) {
          return label = seatLabelChar + (column-1);
        } else if (row <=5 && column >= 11) {
          return label = seatLabelChar + (column-3);
        } else if (row <= 5) {
          return label = seatLabelChar + (column-2);
        } else {
          return label = seatLabelChar + column
        }

        // return label;
        
    },
    },
    legend : {
    node : $('#legend'),
        items : [
        [ 'f', 'available',   'Available' ],
        [ 'f', 'unavailable', 'Already Booked'],
        [ 'f', 'selected', 'Your Seat'],
        ]         
    },
    click: function () {
    if (this.status() == 'available') {
        if ((selected_seat.length + 1) <= jml_seat) {
          //let's create a new <li> which we'll add to the cart items
          $('<span> '+this.settings.label+'</span>')
          .attr('id', 'cart-item-'+this.settings.id)
          .data('seatId', this.settings.id)
          .appendTo($cart);

          selected_seat.push(this.settings.id);
          selected_seat_no.push(this.settings.label)
          /*
          * Lets up<a href="https://www.jqueryscript.net/time-clock/">date</a> the counter and total
          *
          * .find function will not find the current seat, because it will change its stauts only after return
          * 'selected'. This is why we have to add 1 to the length and the current seat price to the total.
          */
          $counter.text(sc.find('selected').length+1);
          price = recalculateTotal(sc)+this.data().price
          $total.text(formatRupiah(recalculateTotal(sc)+this.data().price));
          tiket = this.data().classes
          updateButtonStatus()

          return 'selected';
        } else {
          $('.seatCharts-seat:available').prop('disabled', true);

        }

          
          
    } else if (this.status() == 'selected') {
        selected_seat.pop(this.settings.id)
        selected_seat_no.pop(this.settings.id)
        //update the counter
        $counter.text(sc.find('selected').length-1);
        //and total
        price = (recalculateTotal(sc)-this.data().price)
        $total.text(formatRupiah(recalculateTotal(sc)-this.data().price));
    
        //remove the item from our cart
        $('#cart-item-'+this.settings.id).remove();
        updateButtonStatus()
    
        //seat has been vacated
        return 'available';
    } else if (this.status() == 'unavailable') {
        //seat has been already booked
        return 'unavailable';
    } else {
        return this.style();
    }
    }
});


//this will handle "[cancel]" link clicks
$('#selected-seats').on('click', '.cancel-cart-item', function () {
    //let's just trigger Click event on the appropriate seat, so we don't have to repeat the logic here
    sc.get($(this).parents('li:first').data('seatId')).click();
});

fetch('http://127.0.0.1:4000/get-unavailable-Seat/'+schedule_id)
    .then(response => {
        if (!response.ok) {
        throw new Error('Terjadi kesalahan saat mengambil data.');
        }
        return response.json();
    })
    .then(data => {
        sc.get(data).status('unavailable')
    })
    .catch(error => {
        console.error('Error:', error.message);
    });

//let's pretend some seats have already been booked
// sc.get(['1_5', '4_6', '7_11', '7_10']).status('unavailable');

document.addEventListener('change', function(event) {
    if (event.target.matches('.form-check-input')) {
        checkedDrink = event.target.value;
        // drink_name = 
        console.log($('#drink-name').val())
        updateButtonStatus()
    }
});

});

function recalculateTotal(sc) {
var total = 0;

//basically find every selected seat and sum its price
sc.find('selected').each(function () {
total += this.data().price;
});

return total;
};

// ------------ Akhir Seat -------------

let schedule_detail = () => {
  let data = {'schedule_id' : schedule_id}

  let options = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json' 
        },
        body: JSON.stringify(data)
    };

  fetch('http://127.0.0.1:4000/get-schedule', options)
    .then(response => {
      if (!response.ok) {
        throw new Error('Terjadi kesalahan saat mengirim data.');
      }
      return response.json(data);
    })
    .then(data => {
      let jadwal = data['schedule_detail'][0];
      let $detail_booking = $('#booking-detail');
      let $detail_all = $('#detail_all');
      let $title = $('#title');
      let title = jadwal['title'];
      let cinema = jadwal['nama_theaters'];
      let studio = jadwal['studio'];
      let time = jadwal['jam']
      let harga = jadwal['price']

      $('#movie-title').val()

      $(`<h2 class="fw-bold mb-0" id="title-movie">${title}</h2>`).appendTo($title)
      $(`<h3 id="cinema-name">Cinema : <span class="fw-bold" id="cinema">${cinema}</span></h3>
        <h3 id="studio-name">Studio : <span id="studio" class="fw-bold">${studio}</span></h3>
        <h3 id="datetime">
            <span id="date">Date : <span class="fw-bold">${tanggal}</span></span> |
            <span id="time">Time : <span class="fw-bold">${time}</span></span>
        </h3>
        `).appendTo($detail_all)
    })
    .catch(error => {
      console.log('Error:', error.message);
    });
}


let drinkList = () => {
    fetch('http://127.0.0.1:4000/get-drink',{
    method: 'POST',})
        .then(response => {
            if (!response.ok) {
                throw new Error('Terjadi kesalahan saat mengambil data.');
            }
            return response.json();
        })
        .then(response => {
            const drink_list = document.getElementById('drink-list');
            let content = '';
            response.drink.forEach(drink => { 
                content += `
                    <div class="minuman mt-3">
                        <div class="row">
                            <div class="col-2 d-flex justify-content-center">
                                <img class="img-fluid border rounded-3" src="static/images/drink/${drink.image_drink}" alt="" width="100px">
                            </div>
                            <div class="col-9">
                                <p class="fs-6">${drink.drink_name}</p>
                            </div>
                            <div class="col d-flex justify-content-center align-items-center">
                                <div class="form-check">
                                    
                                    <input class="form-check-input" type="checkbox" value="${drink.id_drink}" id="flexCheckDefault">
                                    
                                    
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            drink_list.innerHTML = content;
        })
        .catch(error => {
            console.error('Error:', error.message);
        });
};


// console.log($('.drink-name').text())



let save_booking = () => { 
    fetch('http://127.0.0.1:5000/login-status', { method: 'POST'})
      .then(response => {
          if (!response.ok) {
              throw new Error('Terjadi kesalahan saat mengirim data.');
          }
          return response.json();
      })
      .then(result => {
            let data = {
                'user_id' : result.user_id,
                'id_schedule' : schedule_id,
                'id_drink' : checkedDrink,
                'id_seat' : selected_seat,
                'total' : price,
                'no_seat' : selected_seat_no
            };

            let options = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify(data)
            };

            fetch('http://127.0.0.1:4000/save-booking', options)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Terjadi kesalahan saat mengirim data.');
                    }
                    return response.json(data);
                })
                .then(data => {
                    window.location.href = `/tickets?booking_id=${data.booking_id}`;
                })
                .catch(error => {
                    console.log('Error:', error.message);
                });
      })
      .catch(error => {
          console.log('Error:', error.message);
      });
};


function payment() {
    console.log($('.card-body').width())
    $('#main-card').addClass("col-md-6");
    $('#main-container').addClass("d-flex");
    $('#main-container').addClass("justify-content-center");
    $('#main-body').empty();
    $('.card-footer').remove();
    // $('.card-body').append('<div id="snap-container"></div>').css('width', $('.card-body').width());
    $('#btn-container').empty();

    var cardBodyWidth = $('.card-body').width();
    var snapContainer = $('<div id="snap-container"></div>').css('width', cardBodyWidth);
    $('.card-body').append(snapContainer);


    let items = {
        'id' : selected_seat_no,
        'price' : price,
        'quantity' : selected_seat.length, 
        'name' : `Tiket Reguler `
    }

    let subtotal = price 

    

    fetch('https://a4a2-202-51-208-50.ngrok-free.app/login-status', { method: 'POST'})
      .then(response => {
          if (!response.ok) {
              throw new Error('Terjadi kesalahan saat mengirim data.');
          }
          return response.json();
      })
      .then(result => {
            let data = {
                'items' : items, 
                'subtotal' : subtotal,
                'user_id' : result.user_id,
                'id_drink' : checkedDrink,
                'id_schedule' : schedule_id,
                'id_seat' : selected_seat
            }
            console.log(data)

            let options = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify(data)
            };

            fetch('http://127.0.0.1:4000/token-transaction', options)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Terjadi kesalahan saat mengirim data.');
                    }
                    return response.json(data);
                })
                .then(token => {
                   window.snap.embed(token, { 
                        embedId: 'snap-container'
                    });
                })
                .catch(error => {
                    console.log('Error:', error.message);
                });
      })
      .catch(error => {
          console.log('Error:', error.message);
      });

    // window.snap.embed('YOUR_SNAP_TOKEN', {
    //     embedId: 'main-body'
    // });
}



$('#confirm-btn').on('click', () => {
    payment()
//   save_booking();
  // window.open(`/tickets?id_movie=${id_movie}`, '_blank');
});;

