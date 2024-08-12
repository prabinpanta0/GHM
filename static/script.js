document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-filler-form');
    const startButton = document.getElementById('start-button');
    const stopButton = document.getElementById('stop-button');
    const statusDiv = document.getElementById('status');

    let intervalId;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = document.getElementById('url').value;
        const iterations = document.getElementById('iterations').value;

        startButton.disabled = true;
        stopButton.disabled = false;

        await fetch('/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, iterations }),
        });

        intervalId = setInterval(updateStatus, 1000);
    });

    stopButton.addEventListener('click', async () => {
        await fetch('/stop', { method: 'POST' });
        startButton.disabled = false;
        stopButton.disabled = true;
        clearInterval(intervalId);
    });

    async function updateStatus() {
        const response = await fetch('/status');
        const data = await response.json();
        
        statusDiv.innerHTML = `
            <p>Total Iterations: ${data.total_iterations}</p>
            <p>Responses Sent: ${data.responses_sent}</p>
            <p>Errors: ${data.errors}</p>
            <p>Iterations Left: ${data.iterations_left}</p>
            <h3>Environment Status:</h3>
            <ul>
                ${data.environment_status.map(status => `<li>${status}</li>`).join('')}
            </ul>
        `;
    }
});