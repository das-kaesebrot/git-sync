package utility

import (
	"fmt"
	"log/slog"
	"net/url"
	"os"
)

func IsUrl(str string) bool {
	u, err := url.Parse(str)
	return err == nil && u.Scheme != "" && u.Host != ""
}

func HandleErr(msg string, err error) {
	slog.Error(msg, "err", err)
	os.Exit(1)
}

func CheckFileAccess(path string) error {
	// doesnt't exist -> not read/writeable
	if _, err := os.Stat(path); err != nil {
		return err
	}

	file, err := os.OpenFile(path, os.O_RDONLY, 0)
	if err != nil {
		return err
	}
	defer file.Close()

	return nil
}

// Prepends elements to a slice. If necessary, the slice is recreated if the underlying capacity doesn't fit.
// Abridged from this blog article: https://go.dev/blog/slices#append-an-example
func Prepend[T any](slice []T, elems ...T) []T {
	total := len(slice) + len(elems)
	if total > cap(slice) {
		newSize := total*3/2 + 1
		newSlice := make([]T, total, newSize)
		copy(newSlice, slice)
		slice = newSlice
	}
	slice = slice[:total]
	copy(slice[len(elems):], slice)
	copy(slice[0:], elems)
	return slice
}

// log out pointers for debug purposes.
func LogPtr[T any](ptr *T) {
	slog.Debug(fmt.Sprintf("Pointer debugging: %T %v %p %v", ptr, &ptr, ptr, *ptr))
}
