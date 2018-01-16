set :application, "dictionaries"
set :repository,  "git@bender.zedge.net:dictionaries.git"

set :scm, :git
set :branch, 'master'
set :deploy_via, :remote_cache
set :git_enable_submodules, 1

ssh_options[:port] = 4000
ssh_options[:forward_agent] = true

set :deploy_to, "/usr/local/sources/dictionaries"

role :app, *((1..6).map {|i| sprintf("hdp%02d.zedge.net", i)})

# Capistrano didn't want to create the releases directory so we do it manually
before(:deploy) do
  run "[[ -d /usr/local/sources/dictionaries/releases ]] || mkdir -p /usr/local/sources/dictionaries/releases"
end
