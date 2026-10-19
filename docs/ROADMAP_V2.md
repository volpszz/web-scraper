# Planejamento da v2 — scraping com autenticação

**Estado: proposta para o futuro. Não implementado na v1.0.0. Sem data de entrega definida.**

A v1 extrai título e links de uma página acessível sem login e salva JSON. O objetivo da v2 é permitir essa coleta em páginas autenticadas de sistemas próprios ou com autorização explícita. Autenticação será uma nova etapa anterior à extração, não uma tentativa de contornar controles de acesso.

## 1. Escopo inicial proposto

Começar com um site de laboratório controlado e um fluxo de login por formulário HTTP:

1. Criar uma `requests.Session` para reutilizar conexão e cookies.
2. Acessar o formulário para obter cookies iniciais e, quando necessário, um token CSRF.
3. Ler as credenciais com segurança, sem imprimir a senha ou colocá-la em argumentos de processo, URL, arquivo versionado ou JSON de resultado. Para uso interativo, avaliar `getpass.getpass()`.
4. Enviar o formulário para um endpoint de autenticação previamente configurado e permitido.
5. Confirmar o login por um indicador específico daquele site ou por um recurso protegido; `200 OK` sozinho não confirma autenticação.
6. Buscar a página protegida usando a mesma sessão.
7. Reutilizar as funções de extração depois de verificar status, tipo de conteúdo e evidência de sessão válida.
8. Exportar somente os dados solicitados e autorizados; encerrar a sessão e, se suportado, executar logout.

Fechar o cliente limpa os recursos locais, mas não garante invalidar a sessão no servidor. O logout depende do protocolo do site.

## 2. Não prometer login universal

Cada aplicação pode usar nomes de campos, tokens, endpoints e indicadores diferentes. Antes de implementar, será necessário escolher o primeiro site/fixture suportado e documentar seu contrato. A arquitetura pode usar adaptadores específicos se houver uma segunda integração real que justifique isso.

Não incluir no primeiro incremento:

- Bypass de MFA, CAPTCHA, SSO, bloqueios ou restrições do serviço.
- Descoberta ou tentativa de senhas, enumeração de contas ou escalada de privilégios.
- Persistência automática de cookies/tokens entre execuções.
- Autenticação de qualquer site sem configuração específica.
- Navegador automatizado por padrão; Playwright/Selenium só devem ser avaliados se o fluxo autorizado depender de JavaScript.
- Crawling autenticado de múltiplas páginas sem uma política adicional de destinos e limites.

## 3. Alterações de arquitetura a avaliar

Separar cliente HTTP/sessão, fluxo de autenticação, extração e apresentação. As funções puras de extração não precisam saber a senha ou gerenciar cookies.

A interface de `fetch_page()` pode receber um cliente HTTP, mantendo o modo anônimo como padrão. Só decidir a assinatura final depois de escrever os testes da primeira integração; isto é um plano, não uma API já existente.

A v1 imprime preview do corpo e mensagens de exceção do `requests`, que podem incluir URLs. **Não reutilizar esse diagnóstico indiscriminadamente em páginas autenticadas.** O modo autenticado deve omitir o preview por padrão e sanitizar URLs, queries e mensagens que possam conter identificadores ou tokens.

O JSON pode conter dados pessoais e links sensíveis mesmo sem senha. Definir minimização dos campos, permissões do arquivo, política de retenção e consentimento antes de salvar. Estar no `.gitignore` não é proteção de confidencialidade.

## 4. Regras de segurança e operação

- Manter verificação TLS habilitada fora do laboratório local; nunca recomendar `verify=False` como solução.
- Nunca versionar senhas, cookies de sessão, tokens CSRF, respostas de login reais ou dados privados como fixtures.
- Usar somente credenciais sintéticas nos testes, em um servidor local sem acesso a contas reais.
- Restringir destinos permitidos para a integração, incluindo endpoints de login e redirecionamentos. Não encaminhar segredos a origens externas.
- Tratar redirecionamento de volta ao login como possível expiração, não como coleta bem-sucedida.
- Evitar retries de login automáticos e ilimitados, que podem bloquear a conta ou repetir ações.
- Respeitar 401/403/429 e as regras do site. Não tentar outro usuário quando faltar autorização.
- Diferenciar autenticação (quem é o usuário) de autorização (quais recursos ele pode acessar).
- Se a ferramenta virar serviço, projetar controles de SSRF, isolamento e limites de recursos separadamente. A validação da v1 não oferece essa proteção.

## 5. Critérios de aceitação propostos

- [ ] Coleta anônima da v1 continua funcionando sem credenciais.
- [ ] Login válido no laboratório permite buscar uma página protegida e exportar o resultado correto.
- [ ] Senha inválida é informada sem exportar a página de login como resultado.
- [ ] Token CSRF ausente ou incorreto é tratado de forma explícita.
- [ ] Sessão expirada é detectada, inclusive quando o servidor redireciona para uma página de login com status final 200.
- [ ] Redirecionamentos para origens não permitidas são bloqueados antes de enviar segredos.
- [ ] Timeout, falha de conexão, status de erro e logout têm cobertura em servidor local.
- [ ] Testes verificam que senhas, cookies, tokens e corpos privados não aparecem na saída, nas exceções exibidas ou no JSON.
- [ ] Erros não sobrescrevem o último resultado válido antes da etapa de escrita; avaliar escrita atômica para proteger também falhas durante a gravação.
- [ ] README e guia explicam o contrato específico de autenticação e suas limitações.

## 6. Decisões ainda abertas

1. Qual aplicação própria/autorizada será a primeira integração?
2. O site usa formulário clássico, API com token ou JavaScript obrigatório?
3. Qual evidência confirma login e qual identifica expiração?
4. Como o usuário informará a configuração sem expor segredos?
5. Quais dados protegidos realmente precisam ser exportados e por quanto tempo?
6. Quais origens e redirecionamentos são permitidos?

Sequência sugerida: fixture local de autenticação → testes de sessão/CSRF → cliente de sessão → diagnóstico seguro → integração específica → exportação → atualização do guia. Não é necessário implementar toda essa sequência agora: a v1 permanece estável e independente.
