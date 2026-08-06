function isDateNotInPast(date) {
    const inputDate = new Date(date);
    const today = new Date();
    // Set time to 00:00:00 for both dates to compare only the date part
    inputDate.setHours(0, 0, 0, 0);
    today.setHours(0, 0, 0, 0);
    return inputDate >= today;
}

// Example usage:
// console.log(isDateNotInPast('2024-06-10')); // true if today or future, false if past


