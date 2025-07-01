#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure logs directory exists
mkdir -p logs
# Ensure short_term_memory directory exists
mkdir -p short_term_memory
# Ensure long_term_memory directory exists
mkdir -p long_term_memory

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to kill process on a port
kill_port() {
    local port=$1
    local pid=$(sudo lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        print_warning "Killing process on port $port (PID: $pid)"
        sudo kill -9 $pid 2>/dev/null
        sleep 2
    fi
}

# Function to check if port is available
check_port() {
    local port=$1
    if sudo lsof -i:$port >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is free
    fi
}

# Function to find available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    while ! check_port $port; do
        port=$((port + 1))
        if [ $port -gt $((start_port + 100)) ]; then
            print_error "Could not find available port starting from $start_port"
            exit 1
        fi
    done
    echo $port
}

# Function to setup environment
setup_environment() {
    print_status "Setting up Python environment..."
    
    if [ ! -d ".venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    print_status "Activating virtual environment and installing dependencies..."
    source .venv/bin/activate
    pip install -U pip
    pip install -e .
    
    print_success "Environment setup complete!"
}

# Function to start Qdrant (using Docker but isolated)
start_qdrant() {
    print_status "Starting Qdrant vector database..."
    
    # Kill any existing Qdrant containers
    docker stop qdrant-local 2>/dev/null || true
    docker rm qdrant-local 2>/dev/null || true
    
    # Find available port for Qdrant
    QDRANT_PORT=$(find_available_port 6333)
    print_status "Qdrant will run on port $QDRANT_PORT"
    
    # Start Qdrant
    docker run -d --rm --name qdrant-local -p $QDRANT_PORT:6333 -v $(pwd)/long_term_memory:/qdrant/storage qdrant/qdrant:latest
    
    if [ $? -eq 0 ]; then
        print_success "Qdrant started successfully on port $QDRANT_PORT"
        echo $QDRANT_PORT > logs/qdrant_port
    else
        print_error "Failed to start Qdrant"
        exit 1
    fi
}

# Function to start Chainlit service
start_chainlit() {
    print_status "Starting Chainlit service..."
    
    # Kill any process on Chainlit port
    kill_port 8000
    
    # Find available port
    CHAINLIT_PORT=$(find_available_port 8000)
    print_status "Chainlit will run on port $CHAINLIT_PORT"
    
    # Get Qdrant port
    QDRANT_PORT=$(cat logs/qdrant_port 2>/dev/null || echo "6333")
    
    # Start Chainlit service in background
    source .venv/bin/activate
    QDRANT_PORT=$QDRANT_PORT chainlit run src/ai_companion/interfaces/chainlit/app.py --host 0.0.0.0 --port $CHAINLIT_PORT > logs/chainlit.log 2>&1 &
    CHAINLIT_PID=$!
    echo $CHAINLIT_PID > logs/chainlit.pid
    echo $CHAINLIT_PORT > logs/chainlit_port
    
    sleep 5
    if kill -0 $CHAINLIT_PID 2>/dev/null; then
        print_success "Chainlit service started successfully on port $CHAINLIT_PORT"
    else
        print_error "Failed to start Chainlit service"
        cat logs/chainlit.log
        exit 1
    fi
}

# Function to show status
show_status() {
    print_status "Service Status:"
    echo "=================="
    
    # Qdrant
    if docker ps | grep -q qdrant-local; then
        QDRANT_PORT=$(cat logs/qdrant_port 2>/dev/null || echo "Unknown")
        print_success "Qdrant: Running on port $QDRANT_PORT"
    else
        print_error "Qdrant: Not running"
    fi
    
    # Chainlit
    if [ -f logs/chainlit.pid ] && kill -0 $(cat logs/chainlit.pid) 2>/dev/null; then
        CHAINLIT_PORT=$(cat logs/chainlit_port 2>/dev/null || echo "Unknown")
        print_success "Chainlit: Running on port $CHAINLIT_PORT"
    else
        print_error "Chainlit: Not running"
    fi
    
    echo ""
    print_status "Access URLs:"
    if [ -f logs/chainlit_port ]; then
        echo "  Chainlit UI: http://localhost:$(cat logs/chainlit_port)"
    fi
}

# Function to stop all services
stop_all() {
    print_status "Stopping all services..."
    
    # Stop Chainlit
    if [ -f logs/chainlit.pid ]; then
        kill $(cat logs/chainlit.pid) 2>/dev/null || true
        rm -f logs/chainlit.pid logs/chainlit_port
        print_success "Chainlit service stopped"
    fi
    
    # Stop Qdrant
    docker stop qdrant-local 2>/dev/null || true
    docker rm qdrant-local 2>/dev/null || true
    rm -f logs/qdrant_port
    print_success "Qdrant service stopped"
    
    print_success "All services stopped!"
}

# Function to show logs
show_logs() {
    local service=$1
    case $service in
        chainlit)
            if [ -f logs/chainlit.log ]; then
                tail -f logs/chainlit.log
            else
                print_error "Chainlit log file not found"
            fi
            ;;
        *)
            print_error "Usage: $0 logs [chainlit]"
            ;;
    esac
}

# Main script logic
case "${1:-start}" in
    start)
        print_status "Starting Multi-Model Chatbot services..."
        setup_environment
        start_qdrant
        start_chainlit
        echo ""
        show_status
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 2
        $0 start
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs $2
        ;;
    setup)
        setup_environment
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|setup}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all services"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  status  - Show service status"
        echo "  logs    - Show logs (usage: $0 logs [chainlit])"
        echo "  setup   - Setup environment only"
        exit 1
        ;;
esac 