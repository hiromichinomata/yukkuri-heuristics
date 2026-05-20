// go/ch02/env_check.go
package main

import (
	"fmt"
	"runtime"
)

func main() {
	fmt.Println("executable:", runtime.Compiler)
	fmt.Printf("version: %s\n", runtime.Version())
	fmt.Println("status: OK")
}
