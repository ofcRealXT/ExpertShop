function actionSelect() {
    let option= document.getElementById("action");
    let command= document.getElementById("command");
  
    if (option.value=== "banuser") {
        command.type= "number";
        command.placeholder= "User id";
    } else if (option.value=== "giveadminrole") {
        command.type= "number";
        command.placeholder= "User id"
    } else if (option.value=== "deleteproduct") {
        command.type= "number";
        command.placeholder= "Product id";
    } else if (option.value== "deletecomment") {
        command.type= "number";
        command.placeholder= "Comment id";
    } else {
        command.type= "text";
        command.placeholder= "Products, comments, users";
    }
  }

function showLocations() {
    document.getElementById('info-locations').style.display= "flex";
}

function hideLocations() {
    document.getElementById('info-locations').style.display= "none";
}

function changeImage() {
    let img= document.getElementById('product-img')
    let vid= document.getElementById('product-vid')
    if (img.style.display== "none") {
        img.style.display= "flex";
        vid.style.display= "none";
    } else {
        img.style.display= "none";
        vid.style.display= "flex";        
    }
}
