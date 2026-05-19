import java.util.Scanner;
public class Autenticacao {
    static boolean fazerLogin(
            Scanner scanner,
            String nomeCliente,
            String senhaCliente
    ) {
        System.out.println("Digite seu nome e senha");

        String loginNome = scanner.next();
        String loginSenha = scanner.next();

        if (loginNome.equals(nomeCliente) && loginSenha.equals(senhaCliente)) {
            System.out.println("Login efetuado com sucesso");
            return true;
        }
        System.out.println("Login inválido");
        return false;
    }
}

