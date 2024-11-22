#include <iostream>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <cstring>

using namespace std;

void game(int sockfd){
    while(1){
        int a, b;
        recv(sockfd, &a, sizeof(a), 0);
        if(a == 0){
            break;
        }
        cout << "Enter your move (1 = Rock, 2 = Paper, 3 = Scissors) or 0 to exit: ";
        cin >> b;
        send(sockfd, &b, sizeof(b), 0);
        if(b == 0){
            break;
        }
        if(a == b){
            cout << "It's a tie!\n";
        }else if((a == 1 && b == 3) ||
                 (a == 2 && b == 1) ||
                 (a == 3 && b == 2)){
            cout << "You lose!\n";
        }else{
            cout << "You win!\n";
        }
    }
}

void udp_connection(int svn, int port){
    char buff[1024];

    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        cout << "Error creating UDP socket.\n";
        exit(-1);
    }

    struct sockaddr_in servadd;
    servadd.sin_family = AF_INET;
    servadd.sin_addr.s_addr = INADDR_ANY;
    servadd.sin_port = htons(port);

    if (::bind(sockfd, (struct sockaddr *)&servadd, sizeof(servadd)) < 0) {
        cout << "Error binding UDP socket.\n";
        close(sockfd);
        exit(-1);
    }
    cout << "Listening on server " << svn << " port " << port << "...\n";

    struct sockaddr_in clientadd;
    socklen_t len = sizeof(clientadd);

    while(1){
        int n = recvfrom(sockfd, buff, 1024, 0, (struct sockaddr*)&clientadd, &len);
        if (n > 0) {
            buff[n] = '\0';
            if(string(buff) == "hello"){
                string reply = "Server " + to_string(svn) + ", Port " + to_string(port);
                sendto(sockfd, reply.c_str(), reply.size(), 0, (struct sockaddr*)&clientadd, len);
                cout << "Sent reply: " << reply << "\n";
            }
            break;
        }
    }

    int n = recvfrom(sockfd, buff, 1024, 0, (struct sockaddr *)&clientadd, &len);
    if (n > 0){
        cout << "Received an invitation. Accept? (y/n): ";
    }
    char choice;
    cin >> choice;
    if(choice == 'n'){
        char msg[] = "n";
        sendto(sockfd, msg, strlen(msg), 0, (struct sockaddr*)&clientadd, len);
    }
    else{
        char msg[] = "y";
        cout << "Connecting...\n";
        sendto(sockfd, msg, strlen(msg), 0, (struct sockaddr*)&clientadd, len);
        n = recvfrom(sockfd, buff, 1024, 0, (struct sockaddr *)&clientadd, &len);
        buff[n] = '\0';
        cout << "Received IP and port: " << buff << "\n";
    }
    close(sockfd);
}

void tcp_connection(const char* ip, int port){
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if(sockfd < 0){
        cout << "Error creating TCP socket.\n";
        exit(-1);
    }

    struct sockaddr_in servadd;
    servadd.sin_family = AF_INET;
    servadd.sin_port = htons(port);
    servadd.sin_addr.s_addr = inet_addr(ip);

    if(connect(sockfd, (struct sockaddr*)&servadd, sizeof(servadd)) < 0){
        cout << "Error connecting to server.\n";
        close(sockfd);
        exit(-1);
    }
    cout << "Connected.\n";
    game(sockfd);
    close(sockfd);
}

int main(){
    int port, n;
    cout << "Enter server: ";
    cin >> n;
    cout << "Enter port: ";
    cin >> port;
    udp_connection(n, port);

    string ip;
    cout << "Enter ip: ";
    cin >> ip;
    cout << "Enter port: ";
    cin >> port;

    tcp_connection(ip.c_str(), port);
    return 0;
}
