document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');

    if (!token) {
        window.location.href = '/index.html';
        return;
    }

    // Requisição para verificar o nível de acesso no Backend
    const response = await fetch('/api/admin/verificar', {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) {
        alert('Acesso restrito apenas para administradores.');
        window.location.href = '/dashboard.html';
        return;
    }

    console.log("Autenticação administrativa validada com sucesso.");
});

// Envio de formulário para cadastrar novos serviços
document.getElementById('form-add-servico').addEventListener('submit', async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');

    const payload = {
        nome: document.getElementById('nome-servico').value,
        categoria: document.getElementById('categoria-servico').value,
        preco_por_mil: parseFloat(document.getElementById('preco-servico').value),
        provedor_api_url: document.getElementById('api-provedor').value,
        provedor_servico_id: parseInt(document.getElementById('id-provedor').value)
    };

    const response = await fetch('/api/admin/servicos', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
    });

    if (response.ok) {
        alert('Serviço adicionado com sucesso!');
        document.getElementById('form-add-servico').reset();
    } else {
        alert('Falha ao adicionar serviço.');
    }
});
