# 🏦 Bank Reis

Meu primeiro projeto Java completo — um sistema bancário de linha de comando desenvolvido com base no livro **"Desenvolvimento Real de Software: Fundamentos em Java"** de Raoul-Gabriel Urma e Richard Warburton.

## 💡 Sobre o projeto

O Bank Reis simula operações básicas de um banco: criação de conta, login, consulta de saldo, depósito e saque. O foco foi aplicar conceitos reais de orientação a objetos com Java, organizando o código em classes com responsabilidades separadas.

## ⚙️ Funcionalidades

- Criar conta com nome e senha
- Autenticação de login
- Consulta de saldo
- Depósito
- Saque com validação de saldo

## 🗂️ Estrutura do projeto

```
src/
├── Main.java           → orquestra o fluxo do programa
├── Cliente.java        → dados e regras do cliente
├── Autenticacao.java   → validação de login
└── Menu.java           → exibição do menu
```

## 🚀 Como rodar

1. Clone o repositório
2. Abra no IntelliJ IDEA (ou outra IDE Java)
3. Execute o arquivo `Main.java`
4. Siga as opções do menu

## 🛠️ Tecnologias

- Java 24
- IntelliJ IDEA

## 📚 O que aprendi

- Orientação a objetos: classes, objetos e campos
- Separação de responsabilidades entre classes
- Fluxo de controle com `switch` e `while`
- Estado de objetos (`logado`, `saldo`, `nome`)
- Validação de entradas do usuário
