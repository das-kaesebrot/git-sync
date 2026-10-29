package config

import (
	"fmt"
	"log/slog"
	"strings"

	"github.com/spf13/viper"
)

type AppConfig struct {
	Config SyncConfig               `mapstructure:"config"`
	Repos  map[string]GitRepoConfig `mapstructure:"repos"`
}

type SyncConfig struct {
	RunType      string `mapstructure:"run_type"`
	CronInterval string `mapstructure:"cron_interval"`
	Keyfile      string `mapstructure:"keyfile"`
}

type GitRepoConfig struct {
	UseGitLFS bool                  `mapstructure:"lfs"`
	Repos     map[string]GitRemotes `mapstructure:"remotes"`
}

type GitRemotes struct {
	IsSource bool   `mapstructure:"source"`
	Url      string `mapstructure:"url"`
}

func ParseConfig(appName string, configFileOverride string) (*AppConfig, error) {
	appName = strings.ToValidUTF8(strings.ToLower(appName), "")

	if configFileOverride != "" {
		viper.SetConfigFile(configFileOverride)
		slog.Info("Using explicit config file path", "configFileOverride", configFileOverride)
	} else {
		searchPaths := []string{
			fmt.Sprintf("/etc/%v/", appName),

			// respect XDG base directory specification https://specifications.freedesktop.org/basedir/latest/#variables
			fmt.Sprintf("$XDG_CONFIG_HOME/%v/", appName),
			fmt.Sprintf("$HOME/.config/%v/", appName),
			".",
		}

		setupDefaultConfigPaths(appName, searchPaths)
		slog.Info("Using default config search paths", "searchPaths", searchPaths)
	}

	err := viper.ReadInConfig()
	if err != nil {
		return nil, err
	}

	c := &AppConfig{}
	err = viper.UnmarshalExact(c)
	if err != nil {
		return nil, err
	}

	return c, nil
}

func setupDefaultConfigPaths(appName string, searchPaths []string) {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")

	for _, searchPath := range searchPaths {
		viper.AddConfigPath(searchPath)
	}

	viper.SetEnvPrefix(appName)
	viper.AutomaticEnv()
}
