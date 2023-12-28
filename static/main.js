function checkImportanceGroup(title, value) {
    let color = '';
    if (value == 'True') {
        color = 'darkred';
    }else {
        color = 'darkblue';
    }
    document.getElementById(`G${title}`).style.borderColor = color;
}

function checkImportanceNotice(title, value) {
    let color = '';
    if (value == 'True'){
        color = 'darkred';
    }else{
        color = 'darkblue'
    }
    document.getElementById(`N${title}`).style.backgroundColor = color;
}