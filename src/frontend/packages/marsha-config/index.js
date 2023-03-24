const path = require('path');

const { packages: packagesConfig } = require('./config.json');

const appPackages = [];
const alias = {};
const moduleNameMapper = {};

for (const packageConfig of packagesConfig) {
  // This is needed for webpack to transpile the packages on the fly
  appPackages.push(
    path.join(__dirname, `../../packages/${packageConfig.folder}`),
  );

  // This is needed for webpack to work with the alias
  alias[packageConfig.alias] = path.resolve(
    __dirname,
    `../../packages/${packageConfig.folder}/src/`,
  );

  // This is needed for jest to work with the alias
  moduleNameMapper[
    `${packageConfig.alias}/(.*)`
  ] = `<rootDir>../../packages/${packageConfig.folder}/src/$1`;
}

module.exports = {
  appPackages,
  alias,
  moduleNameMapper,
};
