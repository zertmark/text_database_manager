use std::env::consts::OS;

#[tokio::main]
async fn main() {
    if OS != "linux" {
        panic!("This program is only available on Linux");
    }
}
