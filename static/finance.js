

let stocks = document.querySelectorAll(".stocks");
let form = document.querySelector("#trade");
let buy = document.querySelector("#buy");
let sell = document.querySelector("#sell");
let symbolInput = document.querySelector("#stock-symbol");
let sharesInput = document.querySelector("#stock-shares");

let register = document.querySelector(".needs-validation");
let passwords = document.querySelector(".password");

function passwordValidation(password) {
    let numbers = 0;

    if (password.length < 8) {
        return false;
    }

    for (i = 0; i < password.length; i++) {
        if (password[i] >= "0" && password[i] <= "9") {
            numbers++;
        }
    }

    if (numbers < 3) {
        return false;
    }

    return true;
}

register.addEventListener("submit", function(event){


    for (let i = 0; i < passwords.length; i++) {
        password = passwords[i].value;

        if (passwordValidation() == false) {
            event.preventDefault();
            event.stopPropagation();
        }
        register.classList.add("was-validated")
    }



}, false);


for (let i = 0; i < stocks.length; i++) {
    stocks[i].addEventListener("click", function(){
        symbolInput.value = stocks[i].dataset.symbol

        for (let j = 0; j < stocks.length; j++) {
            stocks[j].classList.remove("table-active")
        }

        stocks[i].classList.add("table-active");

        if (symbolInput.value && sharesInput.value) {
            buy.disabled = false
            sell.disabled = false
        } else {
            buy.disabled = true
            sell.disabled = true
        }

    });
}


buy.addEventListener("click", function(){

    form.action = "/buy"
    form.submit()

});


sell.addEventListener("click", function(){

    form.action = "/sell"
    form.submit()
});

sharesInput.addEventListener("keyup", function(){
    console.log("BLA")

    if (symbolInput.value && sharesInput.value) {
        buy.disabled = false
        sell.disabled = false
    } else {
        buy.disabled = true
        sell.disabled = true
    }
})

