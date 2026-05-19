import java.util.Scanner;
import java.util.UUID;

public class Cliente {

    long saldo = 0;
    String nome;
    String senha;
    UUID uuid;
    boolean logado = false;


    void registrarCliente(Scanner scanner) {
        System.out.println("Digite seu nome: ");
        this.nome = scanner.next();

        System.out.println("Digite seu senha: ");
        this.senha = scanner.next();

        this.uuid = UUID.randomUUID();

        System.out.println("Registrado com sucesso. Bem vindo " + nome);

    }
    void depositar(long valor){
        this.saldo += valor;
        System.out.println("Deposito concluído! Novo saldo: " + this.saldo);
    }
    boolean sacar(long valor){
        if(valor > this.saldo){
            System.out.println("Saldo insuficiente!");
            return false;
        }
        this.saldo -= valor;
        System.out.println("Saque efetuado! Novo saldo: " + this.saldo);
        return true;

    }
}
