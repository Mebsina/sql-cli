import com.google.inject.Guice;
import com.google.inject.Injector;
import org.opensearch.sql.ppl.PPLService;
import org.opensearch.sql.sql.SQLService;
import py4j.GatewayServer;
import query.QueryExecution;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.regions.providers.DefaultAwsRegionProviderChain;

public class Gateway {

  private PPLService pplService;
  private SQLService sqlService;
  private QueryExecution queryExecution;
  private boolean isInitialized = false;

  public Gateway() {
    // Empty constructor - services will be initialized when OpenSearch CLI connects
  }

  public synchronized String initializeAwsConnection(String hostPort) {
    // hostPort is the AWS OpenSearch endpoint (without https://)
    Region region = new DefaultAwsRegionProviderChain().getRegion();

    try {
      System.out.println(
          "Initializing AWS connection to OpenSearch at " + hostPort + " in region " + region);

      Injector injector = Guice.createInjector(new GatewayModule(hostPort));

      // Initialize services
      this.pplService = injector.getInstance(PPLService.class);
      this.sqlService = injector.getInstance(SQLService.class);
      this.queryExecution = injector.getInstance(QueryExecution.class);

      this.isInitialized = true;
      System.out.println("Successfully initialized AWS connection to " + hostPort);

      return "AWS Endpoint: " + hostPort + "\nRegion: " + region;

    } catch (Exception e) {
      e.printStackTrace();
      return "initializeConnection Error: " + e;
    }
  }

  public synchronized String initializeConnection(
      String host, int port, String protocol, String username, String password, boolean ignoreSSL) {

    try {

      System.out.println(
          "Initializing connection to OpenSearch at " + protocol + "://" + host + ":" + port);

      Injector injector =
          Guice.createInjector(
              new GatewayModule(host, port, protocol, username, password, ignoreSSL));

      // Initialize services
      this.pplService = injector.getInstance(PPLService.class);
      this.sqlService = injector.getInstance(SQLService.class);
      this.queryExecution = injector.getInstance(QueryExecution.class);

      this.isInitialized = true;
      System.out.println(
          "Successfully initialized connection to " + protocol + "://" + host + ":" + port);
      return "Endpoints: " + host + ":" + port;

    } catch (Exception e) {
      e.printStackTrace();
      return "initializeConnection Error: " + e;
    }
  }

  // Defaults to PPL
  public String queryExecution(String query) {
    return queryExecution(query, true);
  }

  public String queryExecution(String query, boolean isPPL) {
    return queryExecution(query, isPPL, "json");
  }

  public String queryExecution(String query, boolean isPPL, String format) {

    // Use the QueryExecution class to execute the query
    return queryExecution.execute(query, isPPL, format);
  }

  public synchronized String disconnect() {

    System.out.println("OpenSearch CLI disconnecting...");

    // Reset the connection state
    this.isInitialized = false;
    this.pplService = null;
    this.sqlService = null;

    return "disconnect: Disconnected successfully.";
  }

  public static void main(String[] args) {
    try {
      System.out.println("Starting Gateway Server...");
      System.out.println(
          "Waiting for OpenSearch CLI to connect and provide OpenSearch host:port"
              + " configuration...");

      Gateway app = new Gateway();

      // default port 25333
      int gatewayPort = 25333;
      GatewayServer server = new GatewayServer(app, gatewayPort);

      server.start();
      System.out.println("Gateway Server Started on port " + gatewayPort);
      System.out.println("Ready to accept connections from OpenSearch CLI.");
    } catch (Exception e) {
      e.printStackTrace();
    }
  }
}
