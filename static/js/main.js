function removeElement(elem_id) {
    const elem = document.getElementById(elem_id);
    console.log(elem);
    elem.style.display = "none";
}

function toggleElementClass(elem_id, className) {
    const elem = document.getElementById(elem_id);
    if (elem.classList.contains(className)) {
        elem.classList.remove(className);
    } else {
        elem.classList.add(className);
    }
}

function toggleHiddenEement(elem_id) {
    toggleElementClass(elem_id, "hidden")
}

function showButtonSpinner(spinner_id, icon_id) {
    const spinner = document.getElementById(spinner_id);
    if (!spinner) {
        return;
    }

    spinner.classList.remove('hidden');
    spinner.classList.add('block');

    if (icon_id) {
        const icon = document.getElementById(icon_id);
        if (icon) {
            icon.classList.add('hidden');
        }
    }
}