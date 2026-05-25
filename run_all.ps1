# Docker Build & Run Script for PPNCKH Project
# Usage: .\docker-build-run.ps1 [command] [options]

param(
    [Parameter(Position = 0)]
    [ValidateSet('build', 'run', 'stop', 'logs', 'clean', 'build-run', 'compose-up', 'compose-down', 'shell')]
    [string]$Command = 'build-run',
    
    [Parameter(Position = 1)]
    [string]$Options = ''
)

$projectName = "ppnckh"
$imageName = "ppnckh:latest"
$containerName = "ppnckh-app"

function Show-Help {
    Write-Host @"
╔════════════════════════════════════════════════════════╗
║         PPNCKH Docker Build & Run Script              ║
╚════════════════════════════════════════════════════════╝

Commands:
  build              - Build Docker image
  run                - Run container in foreground
  stop               - Stop running container
  logs               - View container logs
  clean              - Remove image and container
  build-run          - Build and run (default)
  compose-up         - Start services with docker-compose
  compose-down       - Stop docker-compose services
  shell              - Open interactive shell in container

Examples:
  .\docker-build-run.ps1 build
  .\docker-build-run.ps1 run
  .\docker-build-run.ps1 compose-up
  .\docker-build-run.ps1 shell
"@
}

function Build-Image {
    Write-Host "`nBuilding Docker image: $imageName" -ForegroundColor Cyan
    docker build -t $imageName .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Image built successfully!" -ForegroundColor Green
    } else {
        Write-Host "Build failed!" -ForegroundColor Red
        exit 1
    }
}

function Run-Container {
    Write-Host "`nRunning container: $containerName" -ForegroundColor Cyan
    docker run --name $containerName -it --rm $imageName
}

function Run-Container-Detached {
    Write-Host "`nRunning container (detached): $containerName" -ForegroundColor Cyan
    docker run --name $containerName -d --rm $imageName
    Write-Host "Container started in background!" -ForegroundColor Green
    Write-Host "View logs with: docker logs -f $containerName" -ForegroundColor Yellow
}

function Stop-Container {
    Write-Host "`nStopping container: $containerName" -ForegroundColor Cyan
    docker stop $containerName 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Container stopped!" -ForegroundColor Green
    } else {
        Write-Host "Container not running" -ForegroundColor Yellow
    }
}

function Show-Logs {
    Write-Host "`nContainer logs:" -ForegroundColor Cyan
    docker logs -f $containerName
}

function Clean-Docker {
    Write-Host "`nCleaning Docker resources..." -ForegroundColor Cyan
    
    # Stop container
    docker stop $containerName 2>$null
    
    # Remove container
    docker rm $containerName 2>$null
    
    # Remove image
    docker rmi $imageName 2>$null
    
    Write-Host "Cleanup completed!" -ForegroundColor Green
}

function Compose-Up {
    Write-Host "`nStarting services with docker-compose..." -ForegroundColor Cyan
    docker-compose -p $projectName up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Services started!" -ForegroundColor Green
        Write-Host "View logs: docker-compose logs -f" -ForegroundColor Yellow
    } else {
        Write-Host "Failed to start services!" -ForegroundColor Red
        exit 1
    }
}

function Compose-Down {
    Write-Host "`nStopping docker-compose services..." -ForegroundColor Cyan
    docker-compose -p $projectName down
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Services stopped!" -ForegroundColor Green
    } else {
        Write-Host "Failed to stop services!" -ForegroundColor Red
        exit 1
    }
}

function Open-Shell {
    Write-Host "`n💻 Opening shell in running container..." -ForegroundColor Cyan
    docker exec -it $containerName /bin/bash
}

# Main execution
switch ($Command.ToLower()) {
    'build' {
        Build-Image
    }
    'run' {
        Run-Container
    }
    'stop' {
        Stop-Container
    }
    'logs' {
        Show-Logs
    }
    'clean' {
        Clean-Docker
    }
    'build-run' {
        Build-Image
        Write-Host ""
        Run-Container
    }
    'compose-up' {
        Compose-Up
    }
    'compose-down' {
        Compose-Down
    }
    'shell' {
        Open-Shell
    }
    default {
        Show-Help
    }
}
