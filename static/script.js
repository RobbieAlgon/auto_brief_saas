document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('briefingForm');
    const conversationInput = document.getElementById('conversation');
    const generateButton = document.getElementById('generateButton');
    const resultContainer = document.getElementById('result');
    const briefingContent = document.getElementById('briefingContent');
    const copyButton = document.getElementById('copyButton');
    const downloadButton = document.getElementById('downloadButton');
    const errorMessage = document.getElementById('errorMessage');
    const successMessage = document.getElementById('successMessage');

    // Gerar ID único para o usuário (em produção, isso viria do sistema de autenticação)
    const userId = 'user_' + Math.random().toString(36).substr(2, 9);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Limpar mensagens anteriores
        errorMessage.textContent = '';
        successMessage.textContent = '';
        resultContainer.classList.add('hidden');
        
        // Mostrar loading
        generateButton.disabled = true;
        generateButton.innerHTML = '<span class="loading"></span> Gerando...';
        
        try {
            const response = await fetch('/generate-briefing', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    conversation: conversationInput.value,
                    user_id: userId
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Mostrar resultado
                briefingContent.textContent = JSON.stringify(data, null, 2);
                resultContainer.classList.remove('hidden');
                successMessage.textContent = 'Briefing gerado com sucesso!';
                
                // Salvar briefing
                await saveBriefing(data);
            } else {
                errorMessage.textContent = data.detail || 'Erro ao gerar briefing';
            }
        } catch (error) {
            errorMessage.textContent = 'Erro ao conectar com o servidor';
        } finally {
            // Restaurar botão
            generateButton.disabled = false;
            generateButton.textContent = 'Gerar Briefing';
        }
    });

    copyButton.addEventListener('click', () => {
        const content = briefingContent.textContent;
        navigator.clipboard.writeText(content).then(() => {
            successMessage.textContent = 'Briefing copiado para a área de transferência!';
            setTimeout(() => {
                successMessage.textContent = '';
            }, 3000);
        });
    });

    downloadButton.addEventListener('click', () => {
        const content = briefingContent.textContent;
        const blob = new Blob([content], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'briefing.txt';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    });

    async function saveBriefing(briefing) {
        try {
            const response = await fetch('/briefings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    briefing: briefing,
                    user_id: userId
                })
            });
            
            if (!response.ok) {
                console.error('Erro ao salvar briefing');
            }
        } catch (error) {
            console.error('Erro ao salvar briefing:', error);
        }
    }
}); 