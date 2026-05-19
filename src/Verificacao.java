public class Verificacao {
    static boolean verificarLogin(Cliente cliente){
        if(!cliente.logado){
            System.out.println("Efetue o login primeiro!");
            return false;
        }
        return true;
    }
}
