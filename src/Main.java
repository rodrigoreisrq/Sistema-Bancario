import java.util.Scanner;


public class Main {

    public static void main(String[] args) {

        Scanner scanner = new Scanner(System.in);
        Cliente cliente = new Cliente();


        while (true) {
            Menu.mostrarMenu();
            int resposta = scanner.nextInt();
            if (resposta != 1 && resposta != 2 && resposta != 3 && resposta != 4 && resposta != 5 && resposta != 6) {
                System.out.println("Opção invalida");
            }


            switch (resposta) {

                case 1:
                    cliente.registrarCliente(scanner);
                    break;
                case 2:
                    if(cliente.nome == null){
                        System.out.println("Cadastre-se primeiro!");
                        break;
                    }
                    cliente.logado = Autenticacao.fazerLogin(scanner, cliente.nome, cliente.senha);
                    break;

                case 3:
                    if(!cliente.logado){
                        System.out.println("Efetue o login primeiro!");
                        break;
                    }
                    System.out.println("Seu saldo é: " + cliente.saldo);
                    break;

                case 4:
                    if(!cliente.logado){
                        System.out.println("Efetue o login primeiro!");
                        break;
                    }
                    System.out.println("Quanto deseja depositar? ");
                    long deposito = scanner.nextLong();
                    cliente.depositar(deposito);
                    break;

                case 5:
                    if(!cliente.logado){
                        System.out.println("Efetue o login primeiro!");
                        break;
                    }
                    System.out.println("Quanto deseja sacar? ");
                    long saque = scanner.nextLong();
                    cliente.sacar(saque);
                    break;
                case 6:
                    System.out.println("Volte sempre!");
                    break;

            }if(resposta == 6){
                break;
            }

        }
    }
}
