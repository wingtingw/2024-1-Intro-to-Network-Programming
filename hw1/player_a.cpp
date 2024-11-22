// player a

#include <iostream>
#include <fstream>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstdlib>
#include <netdb.h>
#include <vector>
#include <ifaddrs.h>
#include <time.h>

using namespace std;

vector<int> v;
string get_ip(){
    struct ifaddrs *ifap, *ifa;
    char ip[INET_ADDRSTRLEN];

    getifaddrs(&ifap);
    for (ifa = ifap; ifa != nullptr; ifa = ifa->ifa_next) {
        if (ifa->ifa_addr && ifa->ifa_addr->sa_family == AF_INET) {
            void *addr = &((struct sockaddr_in *)ifa->ifa_addr)->sin_addr;
            inet_ntop(AF_INET, addr, ip, INET_ADDRSTRLEN);
            if (strncmp(ip, "10.", 3) != 0 && strncmp(ip, "127.", 4) != 0) {
                freeifaddrs(ifap);
                return string(ip);
            }
        }
    }
    freeifaddrs(ifap);
    return "No external IP found";
}

void game(int newfd) {
    while (true) {
        int a, b;
        cout << "Enter your move (1 = Rock, 2 = Paper, 3 = Scissors) or 0 to exit: ";
        cin >> a;

        send(newfd, &a, sizeof(a), 0);
        recv(newfd, &b, sizeof(b), 0);
        if(a == 0 || b == 0){
            break;
        }
        if(a == b){
            cout << "It's a tie!\n";
        }
        else if((a == 1 && b == 3) ||
                (a == 2 && b == 1) ||
                (a == 3 && b == 2)){
            cout << "You win!\n";
        }
        else{
            cout << "You lose!\n";
        }
    }
}

void udp_broadcast(){
    char buff[1024];
    int sockfd;
    struct sockaddr_in bcadd;
    if((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0){
        cout << "Error creating socket.\n";
        exit(-1);
    }

    // broadcast
    int bc = 1;
    if(setsockopt(sockfd, SOL_SOCKET, SO_BROADCAST, &bc, sizeof(bc)) < 0){
        cout << "Error broadcasting.\n";
        close(sockfd);
        exit(-1);
    }
    for(int port = 10007; port < 15000; port++){
        bcadd.sin_family = AF_INET;
        bcadd.sin_port = htons(port);  
        bcadd.sin_addr.s_addr = htonl(INADDR_BROADCAST);  

        const char* msg = "hello";
        if(sendto(sockfd, msg, strlen(msg), 0, (struct sockaddr*)&bcadd, sizeof(bcadd)) < 0){
            cout << "Error sending broadcast.\n";
            close(sockfd);
            exit(-1);
        }
    }
    struct sockaddr_in newadd;
    socklen_t len = sizeof(newadd);
    int bk = 2;
    while(bk--){
        int rlen = recvfrom(sockfd, buff, sizeof(buff), 0, (struct sockaddr*)&newadd, &len);
        if(rlen > 0){
            buff[rlen] = '\0';
            cout << buff << "\n";
        }
        if(bk == 0){
            cout << "Press 1 to continue or 0 to exit: ";
            cin >> bk;
        }
    }  
    close(sockfd);
}

void udp_connection(){
    int svn, port;
    cout << "Please select server: ";
    cin >> svn;
    cout << "Please select port: ";
    cin >> port;

    int sockfd;
    struct sockaddr_in servadd;
    if((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0){
        cout << ("Error creating socket.\n");
        exit(-1);
    }

    memset(&servadd, 0, sizeof(servadd));
    servadd.sin_family = AF_INET;
    servadd.sin_port = htons(port);

    switch(svn){
        case 1: servadd.sin_addr.s_addr = inet_addr("140.113.235.151"); break;
        case 2: servadd.sin_addr.s_addr = inet_addr("140.113.235.152"); break;
        case 3: servadd.sin_addr.s_addr = inet_addr("140.113.235.153"); break;
        case 4: servadd.sin_addr.s_addr = inet_addr("140.113.235.154"); break;
    }

    cout << "Sending invitation...\n";
    char msg1[] = "invitation\n";
    if(sendto(sockfd, msg1, strlen(msg1), 0, (struct sockaddr*)&servadd, sizeof(servadd)) < 0) {
        cout << "Error sending message.\n";
        close(sockfd);
        exit(-1);
    }

    char buff[1024] = {0};
    socklen_t len = sizeof(servadd);
    int n = recvfrom(sockfd, buff, 1024, 0, (struct sockaddr*)&servadd, &len);
    if(n < 0){
        cout << "Error receiving.\n";
        close(sockfd);
        exit(-1);
    }

    if(buff[0] == 'y'){
        cout << "Invitation accepted.\n";
        v.push_back(0);

        string ipt = get_ip();
        const char* ip = ipt.c_str();
        cout << "Please enter port number for TCP connection: ";
        cin >> port;
        v.push_back(port);
        cout << "Sending IP and port number...\n";

        char msg2[256];
        snprintf(msg2, sizeof(msg2), "%s:%d", ip, v[1]);

        if(sendto(sockfd, msg2, strlen(msg2), 0, (struct sockaddr*)&servadd, sizeof(servadd)) < 0) {
            cout << "Error sending IP and port.\n";
            close(sockfd);
            exit(-1);
        }

        close(sockfd);
        return;
    }
    else{
        cout << "Invitation rejected.\n";
        v.push_back(1);
        close(sockfd);
        return;
    }
}

void tcp_connection(int port){
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if(sockfd < 0){
        cout << "Error creating TCP socket.\n";
        exit(-1);
    }
    /*
    int on = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &on, sizeof(int));
     */
    struct sockaddr_in servadd;
    servadd.sin_family = AF_INET;
    servadd.sin_addr.s_addr = INADDR_ANY;
    servadd.sin_port = htons(port);
    if (::bind(sockfd, (struct sockaddr *)&servadd, sizeof(servadd)) < 0) {
        cout << "Error binding TCP socket.\n";
        close(sockfd);
        exit(-1);
    }

    cout << "TCP server started at port " << port << " \n";
    if(listen(sockfd, 1) < 0){
        cout << "Error listening.\n";
        exit(1);
    }
    cout << "Waiting for player to connect...\n";

    int newfd;
    struct sockaddr_in clientadd;
    socklen_t len = sizeof(clientadd);
    newfd = accept(sockfd, (struct sockaddr *)&clientadd, &len);
    if (newfd < 0) {
        cout << "Error accepting connection.\n";
        exit(-1);
    }
    cout << "Connected.\n";

    game(newfd);
    close(newfd);
    close(sockfd);
}

int main() {
    udp_broadcast();
    udp_connection();
    if(v[0] == 0) {
        tcp_connection(v[1]);
    }
    return 0;
}
