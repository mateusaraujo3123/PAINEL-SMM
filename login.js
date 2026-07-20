document.addEventListener("DOMContentLoaded", () => {
    
    // 1. FORMULÁRIO DE CADASTRO
    const formCadastro = document.querySelector("#seu-formulario-cadastro"); // Substitua pelo ID real do seu form de cadastro
    if (formCadastro) {
        formCadastro.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(formCadastro);

            try {
                const response = await fetch("/auth/cadastro", {
                    method: "POST",
                    body: formData
                });
                const resultado = await response.json();

                if (response.ok) {
                    alert("Sucesso: " + resultado.mensagem);
                } else {
                    alert("Erro no cadastro: " + (resultado.detail || "Falha ao registrar."));
                }
            } catch (error) {
                console.error("Erro:", error);
            }
        });
    }

    // 2. FORMULÁRIO DE LOGIN
    const formLogin = document.querySelector("#seu-formulario-login"); // Substitua pelo ID real do seu form de login
    if (formLogin) {
        formLogin.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(formLogin);

            try {
                const response = await fetch("/auth/login", {
                    method: "POST",
                    body: formData
                });
                const resultado = await response.json();

                if (response.ok) {
                    window.location.href = resultado.redirecionar; 
                } else {
                    alert("Erro no login: " + (resultado.detail || "Credenciais inválidas."));
                }
            } catch (error) {
                console.error("Erro:", error);
            }
        });
    }
});
