// login.js (Ajuste o evento de Submit do Cadastro)
document.addEventListener("DOMContentLoaded", () => {
    const formCadastro = document.getElementById("formCadastro"); // Certifique-se de que o id no index.html seja este

    if (formCadastro) {
        formCadastro.addEventListener("submit", async (e) => {
            e.preventDefault();

            // Captura dos inputs internos do formulário
            const emailInput = document.getElementById("cadEmail").value;
            const senhaInput = document.getElementById("cadSenha").value;

            try {
                const response = await fetch("/cadastro", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        username: emailInput,
                        password: senhaInput
                    })
                });

                const dados = await response.json();

                if (response.ok) {
                    alert("Conta Premium criada com sucesso!");
                    window.location.href = "/"; // Redireciona para o login ou dashboard
                } else {
                    alert(`Erro: ${dados.detail || "Falha ao realizar cadastro."}`);
                }
            } catch (erro) {
                console.error("Erro na comunicação com a API:", erro);
                alert("Erro crítico de rede. Tente novamente mais tarde.");
            }
        });
    }
});
