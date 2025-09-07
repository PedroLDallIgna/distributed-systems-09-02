package main

import (
	"fmt"
	"time"
	"net/http"
	"encoding/json"
	"database/sql"
	"io"

	_ "github.com/go-sql-driver/mysql"
)

func getRandomWord() string {
	resp, err := http.Get("https://random-words-api.kushcreates.com/api?language=pt-br&words=1")
	if err != nil {
		panic(err.Error())
	}
	defer resp.Body.Close()

	var result []map[string]interface{}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		panic(err.Error())
	}
	json.Unmarshal(body, &result)

	return result[0]["word"].(string)
}

func main() {
	fmt.Println("Starting consumer...")
	db, err := sql.Open("mysql", "user:password@tcp(localhost:3306)/messages")

	if err != nil {
		panic(err.Error())
	}
	defer db.Close()

	err = db.Ping()
	if err != nil {
		panic(err.Error())
	}

	var id int

	fmt.Println("Listening for new events...")
	for {
		tx, err := db.Begin()
		if err != nil {
			panic(err.Error())
		}

		err = tx.QueryRow(`
			SELECT id FROM Events
			WHERE (valor IS NULL OR valor = '') AND (processing IS NULL OR processing = 0)
			ORDER BY id LIMIT 1
			FOR UPDATE
		`).Scan(&id)
		if err != nil {
			tx.Commit()
			time.Sleep(100 * time.Millisecond)
			continue
		}

		res, err := tx.Exec(`
			UPDATE Events
			SET processing = 1
			WHERE id = ?
		`, id)
		if err != nil {
			tx.Rollback()
			panic(err.Error())
		}
		tx.Commit()

		rowsAffected, err := res.RowsAffected()
		if rowsAffected == 0 {
			time.Sleep(100 * time.Millisecond)
			continue
		}

		randomWord := getRandomWord()
		if randomWord != "" {
			_, err = db.Exec(`
				UPDATE Events
				SET valor = ?, processing = 0
				WHERE id = ?
			`, randomWord, id)
			if err != nil {
				panic(err.Error())
			}
			fmt.Printf("Inserted value '%s' in record ID %d\n", randomWord, id)
		}

		time.Sleep(100 * time.Millisecond)
	}
}
