const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Data Contract", function () {
    let Data;
    let data;

    beforeEach(async function () {
        Data = await ethers.getContractFactory("Data");
        data = await Data.deploy();
        await data.deployed();
    });

    it("should set and get speedLimit", async function () {
        await data.setSpeedLimit(60);
        expect(await data.getSpeedLimit()).to.equal(60);
    });

    it("should set and get speed", async function () {
        await data.setSpeed(50);
        expect(await data.getSpeed()).to.equal(50);
    });

    it("should set and get noHornArea", async function () {
        await data.setNoHornArea(true);
        expect(await data.getNoHornArea()).to.equal(true);
    });

    it("should set and get didWeHorned", async function () {
        await data.setDidWeHorned(true);
        expect(await data.getDidWeHorned()).to.equal(true);
    });

    it("should set and get hump", async function () {
        await data.setHump(true);
        expect(await data.getHump()).to.equal(true);
    });

    it("should set and get fourWheeler", async function () {
        await data.setFourWheeler(true);
        expect(await data.getFourWheeler()).to.equal(true);
    });

    it("should set and get seatbelt", async function () {
        await data.setSeatbelt(true);
        expect(await data.getSeatbelt()).to.equal(true);
    });
});