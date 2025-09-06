package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"sync"

	"github.com/gorilla/websocket"
)

type Client struct {
	ID   string
	Conn *websocket.Conn
}

var clients = make(map[string]*Client)
var mu sync.Mutex

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true }, // ⚠️ relajar en dev
}

func handleWS(w http.ResponseWriter, r *http.Request) {
	stackID := r.Header.Get("X-Stack-ID")
	if stackID == "" {
		http.Error(w, "missing X-Stack-ID", http.StatusBadRequest)
		return
	}

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("upgrade error: %v", err)
		return
	}

	client := &Client{ID: stackID, Conn: conn}

	mu.Lock()
	clients[stackID] = client
	mu.Unlock()

	log.Printf("📡 Conectado sentinel: %s", stackID)

	for {
		_, msg, err := conn.ReadMessage()
		if err != nil {
			log.Printf("❌ desconectado %s: %v", stackID, err)
			mu.Lock()
			delete(clients, stackID)
			mu.Unlock()
			return
		}
		log.Printf("📥 [%s] %s", stackID, string(msg))
	}
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/ws", handleWS)
	http.HandleFunc("/healthz", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(200)
		fmt.Fprintln(w, "ok")
	})

	addr := ":" + port
	log.Printf("🚀 event_hub escuchando en %s/ws", addr)
	log.Fatal(http.ListenAndServe(addr, nil))
}
