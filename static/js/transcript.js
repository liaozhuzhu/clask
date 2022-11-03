let shareBtn = document.getElementById("btn-share")
shareBtn.addEventListener("click", () => {
    shareBtn.innerHTML = ""
    navigator.clipboard.writeText(window.location.href);
    console.log(window.location.href)
    let copyConfirm = document.createElement("i")
    copyConfirm.classList.add("fa-solid")
    copyConfirm.classList.add("fa-check")
    shareBtn.innerHTML = "Copied!"
    shareBtn.append(copyConfirm)
    shareBtn.classList.remove("btn-primary")
    shareBtn.classList.add("btn-disabled")
})