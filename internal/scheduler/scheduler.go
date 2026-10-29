package scheduler

import (
	"context"
	"log/slog"
	"strings"

	"github.com/google/uuid"

	"dev.kaesebrot.eu/go/gitsync/internal/gitsync"
	"github.com/go-co-op/gocron/v2"
)

func SetupJobs(ctx context.Context, syncers []gitsync.Syncer) (gocron.Scheduler, error) {
	sched, err := gocron.NewScheduler()
	if err != nil {
		return nil, err
	}

	for _, s := range syncers {
		//logger := slog.Default().With("job", s.Name)
		// format: * * * * *   -> without seconds (5 elements)
		//         * * * * * * -> with seconds (6 elements)
		scheduleSplit := strings.Split(s.Schedule, " ")
		if strings.HasPrefix(scheduleSplit[0], "TZ=") || strings.HasPrefix(scheduleSplit[0], "CRON_TZ=") {
			scheduleSplit = scheduleSplit[1:]
		}
		withSeconds := len(scheduleSplit) > 5

		j, err := sched.NewJob(
			gocron.CronJob(s.Schedule, withSeconds),
			gocron.NewTask(func(contxt context.Context) error {
				return nil
			}),
			gocron.WithName(s.Name),
			gocron.WithContext(ctx),
			gocron.WithEventListeners(
				gocron.BeforeJobRuns(func(jobID uuid.UUID, jobName string) {
					slog.Debug("Running job", "jobID", jobID, "jobName", jobName)
				}),
				gocron.AfterJobRuns(func(jobID uuid.UUID, jobName string) {
					slog.Debug("Job ran successfully", "jobID", jobID, "jobName", jobName)
				}),
				gocron.AfterJobRunsWithError(
					func(jobID uuid.UUID, jobName string, err error) {
						slog.Error("Job returned an error", "jobID", jobID, "jobName", jobName, "err", err)
					},
				),
			),
		)
		if err != nil {
			return nil, err
		}

		slog.Info("Added cronjob to scheduler", "name", s.Name, "id", j.ID(), "schedule", s.Schedule)
	}

	return sched, nil
}
