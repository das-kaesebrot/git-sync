package main

import (
	"context"
	"flag"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"dev.kaesebrot.eu/go/gitsync/internal/config"
	"dev.kaesebrot.eu/go/gitsync/internal/gitsync"
	"dev.kaesebrot.eu/go/gitsync/internal/scheduler"
	"dev.kaesebrot.eu/go/gitsync/internal/utility"
)

var (
	Version = "v0.0.1-dev"
	GitHash = "0000000000000000000000000000000000000000"
)

func parseLogLevelFromString(levelStr string) (slog.Level, error) {
	switch strings.ToLower(levelStr) {
	case "debug":
		return slog.LevelDebug, nil
	case "warn":
		return slog.LevelWarn, nil
	case "error":
		return slog.LevelError, nil
	case "info", "":
		return slog.LevelInfo, nil
	default:
		return slog.LevelInfo, fmt.Errorf("Couldn't parse '%s' as a valid log level, defaulting to 'info'", levelStr)
	}
}

func main() {
	var configFileOverride, logLevelStr string
	flag.StringVar(&configFileOverride, "c", "", "Explicitly set path to config file")
	flag.StringVar(&configFileOverride, "config", "", "Explicitly set path to config file")
	flag.StringVar(&logLevelStr, "l", "", "Set the log level string")
	flag.StringVar(&logLevelStr, "loglevel", "", "Set the log level string")

	flag.Parse()

	if l := os.Getenv("LOG_LEVEL"); l != "" {
		logLevelStr = l
	}

	logLevel, err := parseLogLevelFromString(logLevelStr)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{
		Level: logLevel,
	}))
	slog.SetDefault(logger)
	if err != nil {
		slog.Warn(err.Error())
	}

	slog.Info("Starting up", "version", Version, "gitHash", GitHash)
	slog.Debug("Using slog with specified level", "loglevel", logLevel)

	if configFileOverride != "" {
		err := utility.CheckFileAccess(configFileOverride)
		if err != nil {
			utility.HandleErr("Couldn't open explicitly defined config file!", err)
		}
	}

	_, err = config.ParseConfig("gitsync", configFileOverride)
	if err != nil {
		utility.HandleErr("Error parsing config", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	s, err := scheduler.SetupJobs(ctx, []gitsync.Syncer{})
	if err != nil {
		utility.HandleErr("Error setting up scheduled jobs", err)
	}

	s.Start()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	<-sigChan

	// when you're done, shut it down
	err = s.Shutdown()
	if err != nil {
		utility.HandleErr("Error shutting down jobs", err)
	}
}
