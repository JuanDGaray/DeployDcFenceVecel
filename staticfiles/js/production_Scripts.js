document.getElementById("toggleTableView").addEventListener("click", function() {
    document.getElementById("tableView").classList.remove("d-none");
    document.getElementById("cardView").classList.add("d-none");
});

document.getElementById("toggleCardView").addEventListener("click", function() {
    document.getElementById("cardView").classList.remove("d-none");
    document.getElementById("tableView").classList.add("d-none");
});