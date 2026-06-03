export const formatMovingTime = (seconds: number | null): string => {
    if (seconds === null) return "N/A";

    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60

    return `${h > 0 ? `${h}h ` : ''}${m}m ${s}s`;
}

export const formatPace = (speed: number | null, useImperialDistances: boolean): string => {
    if (speed === null || speed <= 0) return "N/A";

    let minutes : number = 0;
    let seconds : number = 0;

    if (useImperialDistances) {
        const paceSecondsPerMile = 1609.34 / speed; // Convert m/s to s/mile
        minutes = Math.floor(paceSecondsPerMile / 60);
        seconds = Math.round(paceSecondsPerMile % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}/mi`;
    }
        const paceSecondsPerKm = 1000 / speed; // Convert m/s to s/km
        minutes = Math.floor(paceSecondsPerKm / 60);
        seconds = Math.round(paceSecondsPerKm % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}/km`;
}